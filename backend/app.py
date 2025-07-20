from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import threading
import time
from twelve_labs import process_video
from extract_frames import parse_objects_by_timestamp, extract_frames_from_objects
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = '../tempvideos'
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

@app.route('/feng-shuify', methods=['POST'])
def feng_shuify():
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({'error': 'No video_id provided'}), 400
        
        # Find the video file for this video_id
        # For now, we'll use the first video file in the tempvideos folder
        # In a real app, you'd store the mapping between video_id and file path
        video_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.mp4')]
        if not video_files:
            return jsonify({'error': 'No video files found'}), 404
        
        video_path = os.path.join(UPLOAD_FOLDER, video_files[0])
        timestamps_file = "furniture_cleaned.txt"
        output_folder = "pictures"
        
        # Extract frames using the existing functionality
        ts_to_objects = parse_objects_by_timestamp(timestamps_file)
        extract_frames_from_objects(video_path, ts_to_objects, output_folder)
        
        # Run gemini.py to analyze the extracted frames
        try:
            print("Running gemini.py to analyze extracted frames...")
            # Get the current directory (backend/) and run gemini.py from there
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            gemini_path = os.path.join(backend_dir, 'gemini.py')
            
            print(f"Gemini path: {gemini_path}")
            print(f"Working directory: {backend_dir}")
            
            # Run gemini.py from the project root where .env.local is located
            project_root = os.path.dirname(backend_dir)  # hackthesix/
            
            result = subprocess.run([sys.executable, gemini_path], 
                                  capture_output=True, text=True, cwd=project_root)
            
            print(f"Gemini return code: {result.returncode}")
            print(f"Gemini stdout: {result.stdout}")
            print(f"Gemini stderr: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                print("Gemini analysis completed successfully")
                gemini_output = result.stdout
            else:
                print(f"Gemini analysis failed or produced no output")
                print(f"Return code: {result.returncode}")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
                gemini_output = f"Gemini analysis failed - Return code: {result.returncode}, Output: {result.stdout}, Error: {result.stderr}"
                
        except Exception as e:
            print(f"Error running gemini.py: {e}")
            gemini_output = f"Error running gemini: {str(e)}"
        
        return jsonify({
            'message': 'Feng-shuification completed successfully!',
            'frames_extracted': len(ts_to_objects),
            'output_folder': output_folder,
            'gemini_analysis': 'completed'
        })
        
    except Exception as e:
        print(f"Feng-shuify error: {e}")
        return jsonify({'error': f'Feng-shuification failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True)

