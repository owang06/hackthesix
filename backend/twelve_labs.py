from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app, origins=['http://localhost:8000', 'http://127.0.0.1:8000', 'http://localhost:5500', 'http://127.0.0.1:5500'], supports_credentials=True)
UPLOAD_FOLDER = 'tempvideos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working!'})

@app.route('/upload', methods=['POST'])
def upload_video():
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request files: {request.files}")
    print(f"Request form: {request.form}")
    
    if 'video' not in request.files:
        print("No 'video' key found in request.files")
        return jsonify({'error': 'No video part in the request'}), 400
    file = request.files['video']
    if file.filename == '':
        print("Empty filename")
        return jsonify({'error': 'No selected file'}), 400
    
    # Save uploaded file with a unique name
    filename = f"VID{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Return immediately and process video in background
    import threading
    thread = threading.Thread(target=process_video, args=(filepath,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Video uploaded and processing started', 'video_id': filename})

def process_video(video_path):
    # Paste your existing code here but replace video_path with video_path variable
    # For example:

    from dotenv import load_dotenv
    import re
    from twelvelabs import TwelveLabs
    from twelvelabs.models.task import Task

    load_dotenv(dotenv_path=".env.local")
    API_KEY = os.getenv("TLAPI_KEY")

    client = TwelveLabs(api_key=API_KEY)
    import uuid
    INDEX_NAME = str(uuid.uuid4())

    models = [
        {
            "name": "pegasus1.2",
            "options": ["visual", "audio"]
        }
    ]
    index = client.index.create(name=INDEX_NAME, models=models)
    print(f"Index created: id={index.id}, name={index.name}")

    # 3. Upload a video
    with open(video_path, "rb") as f:
        task = client.task.create(
            index_id=index.id,
            file=f  # pass the file object here
        )
    print(f"Created task: id={task.id}, Video id={task.video_id}")

    # 4. Monitor the indexing process
    def on_task_update(task: Task):
        print(f"  Status={task.status}")
    task.wait_for_done(sleep_interval=5, callback=on_task_update)
    if task.status != "ready":
        raise RuntimeError(f"Indexing failed with status {task.status}")
    print(f"The unique identifier of your video is {task.video_id}.")

    # 5. Perform open-ended analysis
    text = client.analyze(
    video_id=task.video_id,  
    prompt="""
    1. Tell me EVERY piece of furniture (eg table, chair, computer, dresser, bed, etc) 
    that you see in this video, along with how many of each you see. 
    2. Give me the latest/last timestamp for each object where at least one of the objects is fully visible in frame
    3. Ensure that the objects are relevant to the floorplan. (For example, coffee machine or string lights is irrelevant)
    4. **Important** Tell me how many items there are total of each object.
    5. Provide a response in a similar style as this template 
    but with temp replaced with the respective objects found, # replaced with their respective timestamps, 
    and 'n' replaced with the respective number of each object found. 
    Also extending or truncating the template for however many items there are:

    In the video, the following pieces of furniture are visible:
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        temp: n - Visible last at [#s (##:##)].
        ...
        ...
        ...
    6. **IMPORTANT** I ONLY WANT 1 TIMESTAMP FOR EACH OBJECT.
    7. **IMPORTANT** MAKE SURE THAT THE OBJECTS ARE VISIBLE AT THE TIMESTAMP PROVIDED.
    8. ***VERY IMPORTANT*** MAKE SURE THAT THE TIMESTAMP PROVIDED FOR EACH OBJECT IS THE LAST TIMEFRAME
    WHERE THE OBJECT IS STILL VISIBLE
    9. ***IMPORTANT*** DOUBLE CHECK IF DESK AND CHAIR ARE STILL VISIBLE AT 3 SECONDS
    10. ***IMPORTANT*** MAKE SURE THAT OBJECTS RELATED TO MORE A GENERAL FURNITURE ARE IGNORED
    (For example, Closet Doors, Closet Hooks, and Closet Hangers are not furniture, especially when there is already a closet and you can just say closet)
    """
    # temperature=0.2
    )
    
    # 6. Process the results
    print(f"{text.data}")

    # Proper regex pattern
    matches = re.findall(r"- (.*?): \d+ - Visible last at \[\d+s \((\d{2}:\d{2})\)\]", text.data)

    # Confirm all matches
    print(f"Matched {len(matches)} lines.")

    with open("furniture_cleaned.txt", "w") as f:
        for obj, timestamp in matches:
            f.write(f"{obj}: {timestamp}\n")

    print("File written.")


if __name__ == "__main__":
    app.run(debug=True)
