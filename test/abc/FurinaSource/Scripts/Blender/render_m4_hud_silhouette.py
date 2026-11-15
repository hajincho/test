"""Renders SK_M4A1.fbx + SM_M4Mag.fbx as a flat white side-view silhouette on a transparent background (muzzle left, stock right, tight bounds) -> Textures/M4HUD_Silhouette.png
and prints / writes the pixel aspect to Data/hud_silhouette.json. Used by the self-made HUD (M_FurinaHUD). Run with Blender 5.2:
blender.exe -b -P render_m4_hud_silhouette.py"""
import bpy, math, json
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
R = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
bpy.ops.import_scene.fbx(filepath=R + r'\FBX\M4\SK_M4A1.fbx')
bpy.ops.import_scene.fbx(filepath=R + r'\FBX\M4\SM_M4Mag.fbx')
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
ys = [p.y for p in pts]; zs = [p.z for p in pts]
wy, wz = max(ys) - min(ys), max(zs) - min(zs)
cy, cz = (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2
print('BBOX_Y', wy, 'BBOX_Z', wz)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (1, 1, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
bpy.ops.object.camera_add(); c = bpy.context.object; c.data.type = 'ORTHO'; sc.camera = c
pad = 1.04; c.data.ortho_scale = max(wy, wz) * pad
c.location = Vector((1.0, cy, cz)); c.rotation_euler = (math.radians(90), 0, math.radians(90))
W = 1600; H = int(round(W * wz / wy))
sc.render.resolution_x = W; sc.render.resolution_y = max(H, 64); sc.render.resolution_percentage = 100
# the orthographic frame is square-scaled to the larger side; fit it tightly in the render: scale applies to the larger render dimension (x here)
c.data.ortho_scale = wy * pad
sc.render.filepath = R + r'\Textures\M4HUD_Silhouette.png'; bpy.ops.render.render(write_still=True)
json.dump(dict(width_px=W, height_px=sc.render.resolution_y, wy=wy, wz=wz, aspect=wy / wz), open(R + r'\Data\hud_silhouette.json', 'w'))
print('SILHOUETTE_DONE')
