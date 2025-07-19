import cv2
import os
import torch
import numpy as np
from ultralytics import YOLO
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image

def extract_frame_at_time(video_path, timestamp_seconds, output_path):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = int(timestamp_seconds * fps)

    if frame_number >= total_frames:
        raise ValueError(f"Timestamp {timestamp_seconds}s exceeds video length of {total_frames / fps:.2f}s")

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()

    if not ret or frame is None:
        raise RuntimeError(f"Failed to read frame at {timestamp_seconds}s (frame {frame_number})")

    cv2.imwrite(output_path, frame)
    cap.release()
    print(f"📸 Frame at {timestamp_seconds}s saved to: {output_path}")
    return output_path

# -------------------------------
# Extract frame from video
video_file = "/Users/whran/Downloads/IMG_1763.jpeg"
timestamp = 0.01  # seconds
frame_path = "extracted_frame.jpg"
image_path = extract_frame_at_time(video_file, timestamp, frame_path)

# -------------------------------
# Load MiDaS model
midas = torch.hub.load("intel-isl/MiDaS", "DPT_Large")
midas.eval()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
midas.to(device)

# MiDaS transforms
midas_transforms = Compose([
    Resize(384),
    ToTensor(),
    Normalize(mean=[0.5], std=[0.5]),
])

# -------------------------------
# Load image
image = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Prepare input for MiDaS
input_image = cv2.resize(image_rgb, (384, 384))
input_pil = Image.fromarray(input_image)
input_tensor = midas_transforms(input_pil).unsqueeze(0).to(device)

# Run depth estimation
with torch.no_grad():
    prediction = midas(input_tensor)
    depth_map = prediction.squeeze().cpu().numpy()
    depth_map = cv2.resize(depth_map, (image.shape[1], image.shape[0]))

# Normalize for display
depth_display = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())

# -------------------------------
# Run YOLOv8 object detection
model = YOLO("yolov8m.pt")  # Make sure this model file exists
results = model(image_path)

# Draw boxes and estimate depth
for box in results[0].boxes:
    cls_id = int(box.cls)
    label = model.names[cls_id]
    x1, y1, x2, y2 = map(int, box.xyxy[0])

    object_depth = depth_map[y1:y2, x1:x2]
    avg_depth = 100.0 - float(np.mean(object_depth))

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
    text = f"{label} (depth={avg_depth:.2f})"
    cv2.putText(image, text, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
# Example camera intrinsics (You must adjust these according to your camera)
# For iPhone, for example:
f_mm = 4.15  # focal length in mm (example)
sensor_width_mm = 6.17  # sensor width in mm (example)
image_width_px = image.shape[1]
image_height_px = image.shape[0]

# Focal length in pixels
f_x = f_mm * image_width_px / sensor_width_mm
f_y = f_x  # assume square pixels

for box in results[0].boxes:
    cls_id = int(box.cls)
    label = model.names[cls_id]
    x1, y1, x2, y2 = map(int, box.xyxy[0])

    # Average depth inside bounding box (in your units)
    object_depth = depth_map[y1:y2, x1:x2]
    avg_depth = float(np.mean(object_depth))

    # Calculate pixel bbox width and height
    bbox_width_px = x2 - x1
    bbox_height_px = y2 - y1

    # Calculate real dimensions (meters)
    real_width_m = (bbox_width_px * avg_depth) / f_x
    real_height_m = (bbox_height_px * avg_depth) / f_y

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
    text = f"{label} W:{real_width_m:.2f}m H:{real_height_m:.2f}m Depth:{avg_depth:.2f}"
    cv2.putText(image, text, (x1, y2 + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

# -------------------------------
# Save outputs
cv2.imwrite("annotated_with_depth.jpg", image)
cv2.imwrite("depth_map_vis.jpg", (depth_display * 255).astype(np.uint8))


print("✅ Done. Saved annotated image and depth map.")


