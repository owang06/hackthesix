import cv2
import os
import torch
import numpy as np
import json
import re
from ultralytics import YOLO
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="AIzaSyBOQGU05bU_oyuiaHmC1VBgvfFH921M0f8")

class MergedSizeEstimator:
    def __init__(self):
        # Load YOLO model
        self.yolo_model = YOLO("yolov8m.pt")
        
        # Load MiDaS model
        self.midas = torch.hub.load("intel-isl/MiDaS", "DPT_Large")
        self.midas.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.midas.to(self.device)
        
        # MiDaS transforms
        self.midas_transforms = Compose([
            Resize(384),
            ToTensor(),
            Normalize(mean=[0.5], std=[0.5]),
        ])
        
        # Camera intrinsics (adjust for your camera)
        self.f_mm = 4.15  # focal length in mm
        self.sensor_width_mm = 6.17  # sensor width in mm
        
        # Gemini model
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    def extract_objects_from_filename(self, filename):
        """Extract object names from filename format: '2.00s - Object1 Object2 Object3.jpg'"""
        base = os.path.splitext(filename)[0]
        parts = base.split(" - ", 1)
        if len(parts) != 2:
            return []
        objects_str = parts[1]
        objects = objects_str.split()
        return objects
    
    def generate_gemini_prompt(self, objects):
        """Generate prompt for Gemini to estimate object dimensions"""
        n = len(objects)
        objects_str = " ".join(objects)
        prompt = (
            f"There are {n} objects visible in this picture: {objects_str}. "
            f"Estimate the real life dimensions of all of these objects IN METERS. "
            f"Be specific, no ranges. "
            f"Also do not tell me its not easily measurable. try your best to estimate. if you cant, tell me its 0. "
            f"Finally, give me answers in the format of a JSON list: "
            f"[{{'object': 'Trash Can', 'length': 0.3, 'width': 0.3, 'height': 0.4}}], "
            f"if any field is unknown enter 0. "
            f"Dont give filler words, only respond with the JSON list."
        )
        return prompt
    
    def parse_gemini_response(self, response_text):
        """Parse Gemini response to extract object dimensions"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data
            else:
                print(f"Could not parse Gemini response: {response_text}")
                return []
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return []
    
    def get_depth_based_estimates(self, image_path):
        """Get size estimates using YOLO + MiDaS depth estimation"""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return []
            
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare input for MiDaS
        input_image = cv2.resize(image_rgb, (384, 384))
        input_pil = Image.fromarray(input_image)
        input_tensor = self.midas_transforms(input_pil).unsqueeze(0).to(self.device)
        
        # Run depth estimation
        with torch.no_grad():
            prediction = self.midas(input_tensor)
            depth_map = prediction.squeeze().cpu().numpy()
            depth_map = cv2.resize(depth_map, (image.shape[1], image.shape[0]))
        
        # Run YOLO detection
        results = self.yolo_model(image_path)
        
        # Calculate camera intrinsics
        image_width_px = image.shape[1]
        image_height_px = image.shape[0]
        f_x = self.f_mm * image_width_px / self.sensor_width_mm
        f_y = f_x
        
        depth_estimates = []
        
        for box in results[0].boxes:
            cls_id = int(box.cls)
            label = self.yolo_model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Average depth inside bounding box
            object_depth = depth_map[y1:y2, x1:x2]
            avg_depth = float(np.mean(object_depth))
            
            # Calculate pixel bbox dimensions
            bbox_width_px = x2 - x1
            bbox_height_px = y2 - y1
            
            # Calculate real dimensions (meters)
            real_width_m = (bbox_width_px * avg_depth) / f_x
            real_height_m = (bbox_height_px * avg_depth) / f_y
            
            # Estimate length (assume it's similar to width for most objects)
            real_length_m = real_width_m
            
            depth_estimates.append({
                'object': label,
                'length': real_length_m,
                'width': real_width_m,
                'height': real_height_m,
                'depth': avg_depth,
                'confidence': float(box.conf[0])
            })
        
        return depth_estimates
    
    def get_gemini_estimates(self, image_path, objects):
        """Get size estimates using Gemini AI"""
        try:
            img = Image.open(image_path)
            prompt = self.generate_gemini_prompt(objects)
            response = self.gemini_model.generate_content(contents=[img, prompt])
            return self.parse_gemini_response(response.text)
        except Exception as e:
            print(f"Error getting Gemini estimates: {e}")
            return []
    
    def merge_estimates(self, depth_estimates, gemini_estimates):
        """Merge depth-based and AI-based estimates intelligently"""
        merged_results = []
        
        # Create lookup dictionaries
        depth_lookup = {est['object'].lower(): est for est in depth_estimates}
        gemini_lookup = {est['object'].lower(): est for est in gemini_estimates}
        
        # Process all objects found by either method
        all_objects = set(depth_lookup.keys()) | set(gemini_lookup.keys())
        
        for obj_name in all_objects:
            depth_est = depth_lookup.get(obj_name)
            gemini_est = gemini_lookup.get(obj_name)
            
            if depth_est and gemini_est:
                # Both methods found the object - merge intelligently
                merged = {
                    'object': depth_est['object'],  # Use YOLO's object name
                    'length': self.weighted_average(depth_est.get('length', 0), gemini_est.get('length', 0), 0.7, 0.3),
                    'width': self.weighted_average(depth_est.get('width', 0), gemini_est.get('width', 0), 0.7, 0.3),
                    'height': self.weighted_average(depth_est.get('height', 0), gemini_est.get('height', 0), 0.7, 0.3),
                    'depth': depth_est.get('depth', 0),
                    'confidence': depth_est.get('confidence', 0),
                    'method': 'merged'
                }
            elif depth_est:
                # Only depth method found it
                merged = depth_est.copy()
                merged['method'] = 'depth_only'
            elif gemini_est:
                # Only Gemini found it
                merged = gemini_est.copy()
                merged['method'] = 'gemini_only'
            
            merged_results.append(merged)
        
        return merged_results
    
    def weighted_average(self, val1, val2, weight1, weight2):
        """Calculate weighted average of two values"""
        if val1 == 0 and val2 == 0:
            return 0
        elif val1 == 0:
            return val2
        elif val2 == 0:
            return val1
        else:
            return (val1 * weight1 + val2 * weight2) / (weight1 + weight2)
    
    def process_image(self, image_path, objects=None):
        """Process a single image and return merged size estimates"""
        print(f"Processing image: {image_path}")
        
        # Get depth-based estimates
        print("Getting depth-based estimates...")
        depth_estimates = self.get_depth_based_estimates(image_path)
        print(f"Depth estimates: {depth_estimates}")
        
        # Get Gemini estimates
        if objects:
            print("Getting Gemini estimates...")
            gemini_estimates = self.get_gemini_estimates(image_path, objects)
            print(f"Gemini estimates: {gemini_estimates}")
        else:
            gemini_estimates = []
        
        # Merge estimates
        if gemini_estimates:
            merged_estimates = self.merge_estimates(depth_estimates, gemini_estimates)
        else:
            merged_estimates = depth_estimates
            for est in merged_estimates:
                est['method'] = 'depth_only'
        
        return merged_estimates
    
    def process_folder(self, pictures_folder="pictures"):
        """Process all images in a folder"""
        results = {}
        
        for filename in os.listdir(pictures_folder):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            filepath = os.path.join(pictures_folder, filename)
            objects = self.extract_objects_from_filename(filename)
            
            if not objects:
                print(f"Skipping {filename}: can't parse objects")
                continue
            
            estimates = self.process_image(filepath, objects)
            results[filename] = estimates
            
            print(f"Results for {filename}:")
            for est in estimates:
                print(f"  {est['object']}: {est['length']:.3f}m x {est['width']:.3f}m x {est['height']:.3f}m ({est['method']})")
            print("-" * 50)
        
        return results

def main():
    estimator = MergedSizeEstimator()
    results = estimator.process_folder()
    
    # Save results to JSON
    with open("merged_size_estimates.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("✅ Done. Results saved to merged_size_estimates.json")

if __name__ == "__main__":
    main() 