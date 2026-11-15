"""Blender headless: imports FBX/Furina_cm.fbx (the file SK_Furina was made from) and dumps armature bones (world head/tail), objects with transforms, meshes (verts, groups, bbox), materials -> Data/furina_inspect.json"""
import bpy, json, math, sys
from mathutils import Vector
SRC = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\Furina_cm.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\furina_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
R = {'src': SRC, 'objects': [], 'armatures': {}, 'meshes': {}}
for o in bpy.context.scene.objects:
    R['objects'].append([o.name, o.type, o.parent.name if o.parent else None, [round(v, 4) for v in o.matrix_world.translation], [round(v, 4) for v in o.scale], [round(math.degrees(a), 1) for a in o.rotation_euler]])
    if o.type == 'ARMATURE':
        R['armatures'][o.name] = {b.name: dict(parent=b.parent.name if b.parent else None, head=[round(v, 4) for v in (o.matrix_world @ b.head_local)], tail=[round(v, 4) for v in (o.matrix_world @ b.tail_local)], roll=round(b.matrix_local.to_euler()[1], 3)) for b in o.data.bones}
    if o.type == 'MESH':
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        R['meshes'][o.name] = dict(verts=len(o.data.vertices), groups=len(o.vertex_groups), bbox_min=[round(min(p[i] for p in pts), 3) for i in range(3)], bbox_max=[round(max(p[i] for p in pts), 3) for i in range(3)],
                                   shape_keys=len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0, materials=[m.name if m else None for m in o.data.materials], modifiers=[m.type for m in o.modifiers])
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('FURINA_INSPECT', len(R['armatures']), len(R['meshes']))
