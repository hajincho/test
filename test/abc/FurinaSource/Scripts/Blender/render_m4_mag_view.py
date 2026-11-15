"""Renders SK_M4A1.fbx (no magazine) and SM_M4Mag.fbx side by side in a side view (workbench) around the magwell -> Data/renders/m4_mag_view.png (rifle in grey, magazine in orange)"""
import bpy, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
R = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
bpy.ops.import_scene.fbx(filepath=R + r'\FBX\M4\SK_M4A1.fbx'); a = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=R + r'\FBX\M4\SM_M4Mag.fbx'); mag = [o for o in bpy.context.scene.objects if o not in a and o.type == 'MESH']
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
for o in sc.objects:
    if o.type == 'MESH': o.color = (1, .45, .1, 1) if o in mag else (.6, .65, .7, 1)
    print('OBJ', o.name, o.type, tuple(round(v, 3) for v in o.dimensions), tuple(round(v, 3) for v in o.location))
for i, (loc, name) in enumerate(((Vector((10, 0, 0)), 'side'),)):
    bpy.ops.object.camera_add(location=(-0.0, 0, 0)); c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = 0.4
    sc.camera = c
    c.location = Vector((1.0, 0, -0.03)); c.rotation_euler = (math.radians(90), 0, math.radians(90))
    sc.render.resolution_x = 1400; sc.render.resolution_y = 900; sc.render.filepath = R + r'\Data\renders\m4_mag_view.png'; bpy.ops.render.render(write_still=True)
