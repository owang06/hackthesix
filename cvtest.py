import cv2

def extract_frame_at_time(video_path, timestamp_seconds, output_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_number = int(timestamp_seconds * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    ret, frame = cap.read()
    if ret:
        cv2.imwrite(output_path, frame)
    cap.release()

extract_frame_at_time("bedroom.mp4", 32.4, "scene.jpg")