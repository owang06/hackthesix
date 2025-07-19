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

# === Rotation and Axis Mapping Configs ===
furniture_rotations = {
    "bed": (math.radians(-90), 0, 0),
    "chair": (0, 0, 0),
    "desk": (0, 0, 0),
    "nightstand": (math.radians(-90), 0, 0),
    "sofa": (0, 0, 0),
    "table": (0, 0, 0),
    "wardrobe": (0, 0, 0),
    "bookshelf": (0, 0, 0)
}

# These define how the original x/y/z inputs from layout map to Blender's X/Y/Z
furniture_coordinate_mapping = {
    "bed": {"x": "z", "y": "y", "z": "x"},
    "chair": {"x": "x", "y": "y", "z": "z"},
    "desk": {"x": "x", "y": "y", "z": "z"},
    "nightstand": {"x": "z", "y": "y", "z": "x"},
    "sofa": {"x": "x", "y": "y", "z": "z"},
    "table": {"x": "x", "y": "y", "z": "z"},
    "wardrobe": {"x": "x", "y": "y", "z": "z"},
    "bookshelf": {"x": "x", "y": "y", "z": "z"}
}

room_size = layout.get("room", {})
room_length = room_size.get("l", 10)
room_width = room_size.get("w", 10)

# === Create Room Floor ===
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

    # coords_dict = {"x": x, "y": y, "z": z}
    # mapping = furniture_coordinate_mapping.get(name, {"x": "x", "y": "y", "z": "z"})
    # remapped_location = (
    #     coords_dict[mapping["x"]],
    #     coords_dict[mapping["y"]],
    #     coords_dict[mapping["z"]]
    # )

    # bpy.ops.object.empty_add(type='PLAIN_AXES', location=remapped_location)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(x, y, 0))
    group = bpy.context.active_object
    group.name = f"{name}_group"
    group.rotation_euler = furniture_rotations.get(name, (0, 0, 0))

    for obj in new_objects:
        obj.select_set(True)
        obj.parent = group
        obj.location -= group.location
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        # ⚠ Here we assume target_w → X, target_l → Y
        scale_object_to_exact_dimensions(obj, target_w, target_l, 1.0)
        
        # Move object so it sits on the floor
        bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_z = min([v.z for v in bbox])
        obj.location.z -= min_z

        
# === Place all furniture ===
for key, value in layout.items():
    if key == "room":
        continue

    place_model(
        name=key,
        x=value["x"],
        y=value["y"],
        z=0,
        rotation_deg=value.get("rotation", 0),
        target_w=value.get("w", 2),
        target_l=value.get("l", 2)
    )
