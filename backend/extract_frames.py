import cv2
import os
import re
from collections import defaultdict

def parse_objects_by_timestamp(timestamps_file):
    # Dict: {timestamp_in_seconds (float): [object_name1, object_name2, ...]}
    ts_to_objects = defaultdict(list)

    pattern = re.compile(r"(.+?) \[(\d+)s .*]")  # matches: ObjectName [2s (00:02)]

    with open(timestamps_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                obj_name = match.group(1).strip()
                ts_sec = 1 + int(match.group(2))
                ts_to_objects[ts_sec].append(obj_name)
            else:
                print(f"Warning: line didn't match expected format: {line}")

    return ts_to_objects

def extract_frames_from_objects(video_path, ts_to_objects, output_folder="pictures"):
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for ts_sec, objects in ts_to_objects.items():
        frame_number = int(ts_sec * fps)
        if frame_number >= total_frames:
            print(f"Warning: timestamp {ts_sec}s exceeds video length, skipping")
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"Warning: failed to extract frame at {ts_sec}s")
            continue

        # Create filename with all objects separated by space
        safe_objects = [obj.replace('/', '-') for obj in objects]  # avoid slashes in filename
        filename = f"{ts_sec:.2f}s - {' '.join(safe_objects)}.jpg"
        output_path = os.path.join(output_folder, filename)

        cv2.imwrite(output_path, frame)
        print(f"Saved frame at {ts_sec}s to {output_path}")

    cap.release()

if __name__ == "__main__":
    video_file = "hackthesix/tempvideos/VID20250719105124.mp4"          # Replace with your video path
    timestamps_file = "output.txt"         # Your furniture objects and timestamps file

    ts_to_objects = parse_objects_by_timestamp(timestamps_file)
    extract_frames_from_objects(video_file, ts_to_objects)