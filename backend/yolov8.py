import numpy as np
import cv2
import torch
from ultralytics import YOLO
from transformers import DPTForDepthEstimation, DPTImageProcessor
from PIL import Image

# --- 1. SETUP MODELS AND SIMULATE VIDEO INPUT ---

# Load the YOLOv8 model for object detection
# 'yolov8n.pt' is a good starting point (YOLOv8 nano)
print("Loading YOLOv8 model...")
yolo_model = YOLO('yolov8n.pt')

# Load the Depth Anything model for depth estimation
print("Loading Depth Estimation model...")
depth_processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
depth_model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")

# Simulate a video file (replace with your actual video path)
video_path = 'tempvideos/IMG_1756.MP4'
try:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file: {video_path}")
except IOError as e:
    print(f"Error: {e}. Using a placeholder for demonstration.")
    cap = None # This will handle the case where the video is not found

# --- 2. THE CORE LOGIC FUNCTIONS ---

def get_frame_at_timestamp(video_capture, timestamp_sec):
    """
    Simulates getting a video frame at a specific timestamp.
    In a real application, you'd use a video processing library to seek.
    """
    if video_capture is None:
        print(f"  - Using placeholder image for timestamp {timestamp_sec:.2f}s")
        # Create a simple black image for demonstration
        placeholder_image = np.zeros((480, 640, 3), dtype=np.uint8)
        # You could draw some simple shapes to test the logic
        cv2.rectangle(placeholder_image, (200, 200), (400, 400), (0, 255, 0), -1) # A green box
        cv2.putText(placeholder_image, f"Time: {timestamp_sec:.2f}s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return placeholder_image
    
    video_capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ret, frame = video_capture.read()
    if not ret:
        print(f"  - Failed to read frame at timestamp {timestamp_sec:.2f}s")
        return None
    return frame

def process_frame(frame):
    """
    Runs both YOLOv8 and the depth model on a single frame.
    Returns a list of dictionaries with object data.
    """
    if frame is None:
        return []

    results = []

    # 1. Run YOLOv8 to get object detections
    yolo_results = yolo_model(frame)
    
    # 2. Run depth estimation model
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    inputs = depth_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        depth_output = depth_model(**inputs)
    
    predicted_depth = depth_output.predicted_depth
    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    ).squeeze().cpu().numpy()
    
    # Normalize depth map to a more usable range (e.g., 0-255)
    depth_map = (prediction - prediction.min()) / (prediction.max() - prediction.min())
    depth_map = (depth_map * 255).astype("uint8")

    # 3. Combine YOLO and depth results
    for result in yolo_results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = yolo_model.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            
            # Get the average depth within the bounding box
            roi_depth = depth_map[y1:y2, x1:x2]
            if roi_depth.size > 0:
                avg_depth = np.mean(roi_depth)
            else:
                avg_depth = -1 # A sentinel value for a bad box
            
            results.append({
                'label': label,
                'confidence': confidence,
                'bbox': [x1, y1, x2, y2],
                'depth_raw': avg_depth, # Depth is a relative value, not a true distance
                'timestamp_sec': None # Will be filled later
            })
    return results

def iou(boxA, boxB):
    """
    Computes Intersection over Union (IoU) of two bounding boxes.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou_val = interArea / float(boxAArea + boxBArea - interArea)
    return iou_val

def prevent_overlap(all_detections, iou_threshold=0.5):
    """
    Merges detections of the same object across multiple frames using IoU.
    
    Args:
        all_detections (list): A list of lists, where each inner list contains
                               detections for a single frame.
        iou_threshold (float): The IoU value above which two detections are
                               considered the same object.

    Returns:
        list: A consolidated list of unique objects.
    """
    if not all_detections:
        return []

    # Start with the detections from the first frame as the initial unique objects
    unique_objects = all_detections[0]

    # Process subsequent frames
    for current_frame_detections in all_detections[1:]:
        new_detections_in_frame = []
        for current_detection in current_frame_detections:
            is_new_object = True
            for unique_obj in unique_objects:
                # Check for overlap based on label and IoU
                if (current_detection['label'] == unique_obj['label'] and
                    iou(current_detection['bbox'], unique_obj['bbox']) > iou_threshold):
                    
                    # Found a match, this is a duplicate detection
                    # Option 1: Keep the one with the highest confidence
                    if current_detection['confidence'] > unique_obj['confidence']:
                        # Replace the old unique object with the new one
                        unique_obj.update(current_detection)
                    is_new_object = False
                    break
            
            if is_new_object:
                new_detections_in_frame.append(current_detection)
        
        # Add any truly new objects from the current frame to the unique list
        unique_objects.extend(new_detections_in_frame)
    
    return unique_objects

## --- 3. Execute the workflow ---

def main():
    # Simulate the output from Twelve Labs
    # This represents the key moments in the video
    print("Simulating Twelve Labs analysis...")
    timestamps = [0.5, 1.0, 1.5, 5.0, 5.5, 10.0] # seconds

    all_frame_detections = []

    for ts in timestamps:
        print(f"\nProcessing timestamp: {ts:.2f}s")
        frame = get_frame_at_timestamp(cap, ts)
        if frame is not None:
            detections = process_frame(frame)
            for d in detections:
                d['timestamp_sec'] = ts # Add timestamp to each detection
            all_frame_detections.append(detections)

    # Now, process all detections to prevent overlap
    print("\nStarting overlap prevention and consolidation...")
    final_unique_objects = prevent_overlap(all_frame_detections, iou_threshold=0.7)
    
    # Print the final, consolidated results
    print("\n--- Final Consolidated Objects ---")
    if not final_unique_objects:
        print("No objects were detected or consolidated.")
    else:
        for i, obj in enumerate(final_unique_objects):
            print(f"Object {i+1}: {obj['label']}")
            print(f"  - Conf: {obj['confidence']:.2f}")
            print(f"  - BBox: {obj['bbox']}")
            print(f"  - Depth (relative): {obj['depth_raw']:.2f}")
            print(f"  - Found at Timestamp: {obj['timestamp_sec']:.2f}s")

if __name__ == "__main__":
    main()