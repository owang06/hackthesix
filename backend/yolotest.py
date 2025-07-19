from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # or yolov8s.pt for more accuracy
results = model("scene.jpg")

for box in results[0].boxes:
    cls_id = int(box.cls)
    label = model.names[cls_id]
    xyxy = box.xyxy[0].tolist()
    print(f"{label}: {xyxy}")