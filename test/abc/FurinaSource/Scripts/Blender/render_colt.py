"""Blender headless: renders Colt_m4A1.fbx objects in different colours (m4a1.001 grey, ammo red, mag_20rnd green) from the side (looking along X), top and front to Data/renders/colt_side.png / colt_top.png / colt_iso.png"""
import bpy, math
from mathutils import Vector
SRC = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\renders'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=SRC)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
cols = {'m4a1.001': (.6, .65, .7, 1), 'ammo': (1, .2, .2, 1), 'mag_20rnd': (.2, .9, .3, 1)}
pts = []
for o in sc.objects:
    if o.type == 'MESH': o.color = cols.get(o.name, (1, 1, 0, 1)); pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)]); ctr = (mn + mx) / 2; size = max((mx - mn))
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.1; sc.camera = cam
sc.render.resolution_x = 1600; sc.render.resolution_y = 900
for name, loc, rot in (('side', (1, 0, 0), (90, 0, 90)), ('top', (0, 0, 1), (0, 0, 0)), ('front', (0, -1, 0), (90, 0, 0))):
    cam.location = ctr + Vector(loc) * (size * 2); cam.rotation_euler = tuple(math.radians(a) for a in rot)
    sc.render.filepath = OUT + r'\colt_%s.png' % name; bpy.ops.render.render(write_still=True)
print('COLT_RENDER', tuple(mn), tuple(mx))
