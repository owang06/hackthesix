import os
import re
import uuid
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task

# Load API Key
load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("TLAPI_KEY")

# 1. Initialize the client
client = TwelveLabs(api_key=API_KEY)

INDEX_NAME = str(uuid.uuid4())

VIDEO_PATH = "tempvideos/VID20250719105124.mp4"

# 2. Create an index
models = [
    {
        "name": "pegasus1.2",
        "options": ["visual", "audio"]
    }
]
index = client.index.create(name=INDEX_NAME, models=models)
print(f"Index created: id={index.id}, name={index.name}")

# 3. Upload a video
with open(VIDEO_PATH, "rb") as f:
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
  1. Tell me EVERY SINGLE furniture object (eg table, chair, computer, dresser, bed, etc) 
  that you see in this video, along with how many of each you see. 
  2. Give me a timestamp for each object where at least one of the objects is fully visible in frame
  3. **Important** Make sure to get every object possible regardless of how small or simple.
  4. **Important** Tell me how many items there are total of each object.
  5. Provide a response in a similar style as this template 
  but with temp replaced with the respective objects found, # replaced with their respective timestamps, 
  and 'n' replaced with the respective number of each object found. 
  Also extending or truncating the template for however many items there are:

  In the video, the following furniture objects are visible:
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    temp: n - Visible at _____ [#s (##:##)].
    ...
    ...
    ...
  6. **IMPORTANT** I ONLY WANT 1 TIMESTAMP FOR EACH OBJECT.
  7. **IMPORTANT** MAKE SURE THAT THE OBJECTS ARE VISIBLE AT THE TIMESTAMP PROVIDED.
  """,
  # temperature=0.2
)
# 6. Process the results
print(f"{text.data}")

matches = re.findall(r"- (\w[\w\- ]*):.*(\[\d+s \(\d+:\d+\)\])", text.data)

with open("output.txt", "w") as f:
    for obj, timestamp in matches:
        f.write(f"{obj} {timestamp}\n")