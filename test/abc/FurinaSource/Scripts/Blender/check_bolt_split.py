"""blender.exe -b --python check_bolt_split.py : FBX/M4/SK_M4A1.fbx(노리쇠 뺀 본체)와 SM_M4Bolt.fbx 를 불러 노리쇠를 0, 뒤로 6.75cm 옮긴 상태를 옆(양쪽)에서 렌더 -> Scratch/bolt_split_<위치>_<면>.png"""
import bpy, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
bpy.ops.import_scene.fbx(filepath=D + r'\FBX\M4\SK_M4A1.fbx', automatic_bone_orientation=False)
body = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pre = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=D + r'\FBX\M4\SM_M4Bolt.fbx')
bolt = [o for o in bpy.context.scene.objects if o not in pre and o.type == 'MESH']
def bb(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]; return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]
print('BODY', bb(body)); print('BOLT', bb(bolt))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 1400; sc.render.resolution_y = 500
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
for o in bolt: o.color = (1, 0.1, 0.1, 1)
for o in body: o.color = (0.7, 0.7, 0.7, 1)
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam; cam_d.type = 'ORTHO'; cam_d.ortho_scale = 0.55
lo, hi = bb(body); lb, hb = bb(bolt); ctr = [(lb[k] + hb[k]) / 2 for k in range(3)]; ctr[1] -= 0.03
# 길이축 찾기
ext = [hi[k] - lo[k] for k in range(3)]; ax = ext.index(max(ext)); print('LENGTH AXIS', ax, ext)
up = 2
side = [k for k in range(3) if k not in (ax, up)][0]
import json
for shift in (0.0, 7.0):
    for o in bolt: o.location = Vector((0, 0, 0)); o.location[ax] = shift * 0.01
    for sgn in (1, -1):
        loc = Vector(ctr); loc[side] += 3 * sgn; cam.location = loc
        d = Vector(ctr) - loc; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = r'%s\Scratch\bolt_split_%s_%s.png' % (D, 'rest' if shift == 0 else 'back', 'p' if sgn > 0 else 'n'); bpy.ops.render.render(write_still=True)
print('CHECK_OK')
