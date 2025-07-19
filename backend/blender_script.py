import bpy
import json
import math

# === CONFIG ===
INPUT_JSON = "backend/layout.json"
EXPORT_PATH = "./room_layout.obj"

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Load layout
with open(INPUT_JSON, "r") as f:
    layout = json.load(f)

room_size = layout.get("room", {})
room_length = room_size.get("l", 10)
room_width = room_size.get("w", 10)

# Create room floor
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.scale = (room_length / 2, room_width / 2, 1)
floor.name = "Room_Floor"

# Add cube for each object
def place_box(name, x, y, w=1, d=1, h=1, rotation_deg=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (w / 2, d / 2, h / 2)
    obj.rotation_euler = (0, 0, math.radians(rotation_deg))

for key, value in layout.items():
    if key == "room":
        continue

    w = value.get("w", 1)
    l = value.get("l", 1)
    place_box(
        name=key,
        x=value["x"],
        y=value["y"],
        w=w,
        d=l,
        rotation_deg=value.get("rotation", 0)
    )

# ✅ Export scene (OBJ exporter must already be enabled in Blender preferences)
# bpy.ops.export_scene.obj(filepath=EXPORT_PATH)
# print(f"✅ Scene exported to: {EXPORT_PATH}")
