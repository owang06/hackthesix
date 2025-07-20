import cv2
import os
import re
from collections import defaultdict
import glob

def get_first_video_file(folder="tempvideos"):
    # Find all video files with .mp4 extension (you can add others if needed)
    video_files = glob.glob(os.path.join(folder, "*.mp4"))
    if not video_files:
        raise FileNotFoundError(f"No video files found in {folder}")
    # Sort files alphabetically or by creation time if you want:
    video_files.sort()
    return video_files[0]

def clear_folder(folder="tempvideos"):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # remove file or link
            elif os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)  # remove folder recursively
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def parse_objects_by_timestamp(timestamps_file):
    # Dict: {timestamp_in_seconds (float): [object_name1, object_name2, ...]}
    ts_to_objects = defaultdict(list)

    pattern = re.compile(r"(.+?) (\d{2}:\d{2})")  # matches: ObjectName 00:02

    with open(timestamps_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                obj_name = match.group(1).strip()
                minutes, seconds = map(int, match.group(2).split(":"))
                ts_sec = minutes * 60 + seconds  # or `1 + minutes * 60 + seconds` if you want the offset
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
    video_folder = "tempvideos"
    video_file = get_first_video_file(video_folder)         # Replace with your video path
    timestamps_file = "furniture_cleaned.txt"         # Your furniture objects and timestamps file

    ts_to_objects = parse_objects_by_timestamp(timestamps_file)
    extract_frames_from_objects(video_file, ts_to_objects, "../pictures")
    # clear_folder(video_folder)