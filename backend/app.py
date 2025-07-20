from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import threading
import time
from twelve_labs import process_video
from extract_frames import parse_objects_by_timestamp, extract_frames_from_objects
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'hackthesix/tempvideos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global status tracking
processing_status = {}
processing_results = {}

def background_process(video_path, video_id):
    try:
        processing_status[video_id] = {
            'status': 'processing',
            'message': 'Starting video analysis...',
            'progress': 0
        }
        
        # Step 1: Twelve Labs processing
        processing_status[video_id]['message'] = 'Analyzing video with Twelve Labs...'
        processing_status[video_id]['progress'] = 25
        process_video(video_path)
        
        # Step 2: Extract frames
        processing_status[video_id]['message'] = 'Extracting frames from video...'
        processing_status[video_id]['progress'] = 75
        
        # Get the video file path for frame extraction
        video_file = video_path
        timestamps_file = "furniture_cleaned.txt"
        output_folder = "pictures"
        
        ts_to_objects = parse_objects_by_timestamp(timestamps_file)
        extract_frames_from_objects(video_file, ts_to_objects, output_folder)
        
        # Step 3: Processing complete
        processing_status[video_id] = {
            'status': 'completed',
            'message': 'Processing completed successfully!',
            'progress': 100
        }
        
        # Store results
        processing_results[video_id] = {
            'frames_extracted': len(ts_to_objects),
            'output_folder': output_folder,
            'timestamps_file': timestamps_file
        }
        
        print(f"Processing finished for {video_path}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        processing_status[video_id] = {
            'status': 'error',
            'message': f'Processing failed: {str(e)}',
            'progress': 0
        }

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video part in the request'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = f"VID{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Generate a unique video ID
    video_id = str(uuid.uuid4())
    
    # Initialize status
    processing_status[video_id] = {
        'status': 'uploaded',
        'message': 'Video uploaded successfully',
        'progress': 0
    }

    # Start video processing in background thread
    thread = threading.Thread(target=background_process, args=(filepath, video_id))
    thread.start()
    
    # Return immediately with video ID
    return jsonify({
        'message': 'Video uploaded. Processing started in background.', 
        'video_path': filepath,
        'video_id': video_id
    })

@app.route('/status/<video_id>', methods=['GET'])
def get_status(video_id):
    """Get the processing status for a video"""
    if video_id not in processing_status:
        return jsonify({'error': 'Video ID not found'}), 404
    
    status = processing_status[video_id].copy()
    
    # Add results if processing is complete
    if status['status'] == 'completed' and video_id in processing_results:
        status['results'] = processing_results[video_id]
    
    return jsonify(status)

@app.route('/extract_frames', methods=['POST'])
def extract_frames_route():
    try:
        data = request.get_json() or {}

        video_path = data.get('video_path', 'hackthesix/tempvideos/VID20250719105124.mp4')
        timestamps_file = data.get('timestamps_file', 'output.txt')
        output_folder = data.get('output_folder', 'pictures')

        # Make sure your parsing and extraction functions are defined or imported here

        ts_to_objects = parse_objects_by_timestamp(timestamps_file)
        extract_frames_from_objects(video_path, ts_to_objects, output_folder)

        return jsonify({'message': f'Frames extracted to {output_folder}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/models/<filename>")
def serve_model(filename):
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "blender_model"))
    return send_from_directory(model_path, filename)

if __name__ == "__main__":
    app.run(debug=True)

