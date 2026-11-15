"""Blender headless: inspects Colt_m4A1.fbx (objects, hierarchy, bounding boxes in metres, vertex counts, materials with their images, armatures/bones) and the geometry axes -> Data/colt_inspect.json"""
import bpy, json, math
from mathutils import Vector
SRC = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
bpy.context.view_layer.update()
R = {'unit_scale': bpy.context.scene.unit_settings.scale_length, 'objects': []}
allpts = []
for o in bpy.context.scene.objects:
    d = dict(name=o.name, type=o.type, parent=o.parent.name if o.parent else None, loc=[round(v, 4) for v in o.matrix_world.translation], scale=[round(v, 4) for v in o.matrix_world.to_scale()],
             rot_deg=[round(math.degrees(a), 1) for a in o.matrix_world.to_euler()])
    if o.type == 'MESH':
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]; allpts += pts
        d.update(verts=len(o.data.vertices), faces=len(o.data.polygons), bbox_min=[round(min(p[i] for p in pts), 4) for i in range(3)], bbox_max=[round(max(p[i] for p in pts), 4) for i in range(3)],
                 materials=[m.name if m else None for m in o.data.materials], groups=len(o.vertex_groups), shape_keys=len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0)
    if o.type == 'ARMATURE': d['bones'] = [(b.name, b.parent.name if b.parent else None, [round(v, 4) for v in (o.matrix_world @ b.head_local)]) for b in o.data.bones][:40]
    R['objects'].append(d)
if allpts: R['overall_bbox'] = [[round(min(p[i] for p in allpts), 4) for i in range(3)], [round(max(p[i] for p in allpts), 4) for i in range(3)]]
mats = {}
for m in bpy.data.materials:
    if m.use_nodes: mats[m.name] = sorted(set(n.image.name for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image))
R['materials'] = mats
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('COLT_INSPECT', len(R['objects']))
