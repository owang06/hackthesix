import bpy
import json
import math
import os
import mathutils

# === CONFIG ===
INPUT_JSON = "backend/layout.json"
FURNITURE_DIR = "furniture"

# === Clear scene ===
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# === Load layout ===
with open(INPUT_JSON, "r") as f:
    layout = json.load(f)

room_size = layout.get("room", {})
room_length = room_size.get("l", 10)
room_width = room_size.get("w", 10)

# === Create room floor ===
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.scale = (room_length, room_width, 1)
floor.name = "Room_Floor"

def scale_object_to_exact_dimensions(obj, target_x, target_y, target_z=1.0):
    if obj.type != 'MESH':
        return

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    current_x = obj.dimensions.x
    current_y = obj.dimensions.y
    current_z = obj.dimensions.z

    scale_x = target_x / current_x if current_x != 0 else 1.0
    scale_y = target_y / current_y if current_y != 0 else 1.0
    scale_z = target_z / current_z if current_z != 0 else 1.0

    obj.scale.x *= scale_x
    obj.scale.y *= scale_y
    obj.scale.z *= scale_z

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def place_model(name, x, y, z, rotation_deg=0, target_w=2.0, target_l=2.0):
    import mathutils

    folder = os.path.join(FURNITURE_DIR, name)
    path = os.path.abspath(os.path.join(folder, "scene.gltf"))

    if not os.path.isfile(path):
        print(f"❌ Missing GLTF for {name}: {path}")
        return

    print(f"📦 Importing {name}")
    before = set(bpy.data.objects)

    bpy.ops.import_scene.gltf('EXEC_DEFAULT', filepath=path)
    after = set(bpy.data.objects)
    new_objects = list(after - before)

    if not new_objects:
        print(f"⚠️ Failed to import {name}")
        return

    # Create group empty at target position
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(x, y, z))
    group = bpy.context.active_object
    group.name = f"{name}_group"

    for obj in new_objects:
        obj.select_set(True)
        obj.parent = group
        obj.location -= group.location

        # Rotate upright
        obj.rotation_euler = (math.radians(-90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        # Scale to match dimensions
        scale_object_to_exact_dimensions(obj, target_w, 1.0, target_l)

# === Place all furniture ===
for key, value in layout.items():
    if key == "room":
        continue

    place_model(
        name=key,
        x=value["x"],
        y=value["y"],
        z = 0,
        rotation_deg=value.get("rotation", 0),
        target_w=value.get("w", 2),
        target_l=value.get("l", 2)
    )
