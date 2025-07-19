from twelvelabs import TwelveLabs

client = TwelveLabs(api_key="tlk_3N7TRXK1EHGJDB29REMD02K96XTJ")

# Create the index (only once)
# index = client.index.create(
#     name="my-bedroom-index-4",
#     models=[{"name": "marengo2.7", "options": ["visual", "audio"]}]
# )
# print(f"Created index: id={index.id} name={index.name}")

# index = client.index.retrieve(name="my-bedroom-index")




# List all your indexes and find the one you want
indexes = client.index.list()

# Pick the one you want by name
index = next((i for i in indexes if i.name == "my-bedroom-index"), None)

if index is None:
    # If not found, create it
    index = client.index.create(
        name="my-bedroom-index",
        models=[{"name": "marengo2.7", "options": ["visual", "audio"]}]
    )
    print(f"Created new index: {index.name} (id={index.id})")
else:
    print(f"Reusing existing index: {index.name} (id={index.id})")



# Upload your local video file using `video_file`
with open("/Users/whran/Downloads/IMG_1756.mp4", "rb") as f:
    task = client.task.create(
        index_id=index.id,
        file=f  # pass the file object here
    )
print(f"Created task: id={task.id}")

# Wait for indexing to complete
task.wait_for_done(sleep_interval=5, callback=lambda t: print(f"  Status={t.status}"))
if task.status != "ready":
    raise RuntimeError(f"Indexing failed with status {task.status}")
print(f"Upload complete. Video ID: {task.video_id}")

# Get analysis results instead of search
analysis = client.analysis.get(task.video_id)

# Find the first time a laptop appears
laptop_clips = [obj for obj in analysis.data["objects"] if "laptop" in obj["label"].lower()]

if not laptop_clips:
    print("No laptop detected.")
else:
    # Sort by starting time
    laptop_clips.sort(key=lambda x: x["start"])
    first = laptop_clips[0]
    print(f"Laptop first appears at {first['start']:.2f}s to {first['end']:.2f}s (confidence={first['confidence']:.2f})")

