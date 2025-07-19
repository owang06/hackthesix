import os
import requests
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task

# Load API Key
load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("TLAPI_KEY")

# 1. Initialize the client
client = TwelveLabs(api_key=API_KEY)


VIDEO_PATH = "<Temp Video Path>"
INDEX_NAME = "<Temp Index Name>"

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
  prompt="Identify the timestamps for when the first laptop appears",
  # temperature=0.2
)
# 6. Process the results
print(f"{text.data}")