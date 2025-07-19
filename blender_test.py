import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cone_add(depth=3, radius1=1, location=(10, 50, 1.5))
