"""Blender headless: inspects Joumae Saori.fbx (armatures, bones with parents and rest head positions, meshes with dimensions / vertex group counts / shape keys / materials) -> Data/saori_inspect.json.
blender.exe -b -P inspect_saori.py"""
import bpy, json, math
from mathutils import Vector
SRC = r'C:\Users\fromj\Downloads\joumae-saori\source\Joumae Saori From Blue Archive\Joumae Saori.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\saori_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
R = {'unit_scale': bpy.context.scene.unit_settings.scale_length, 'objects': [], 'armatures': {}, 'meshes': {}}
for o in bpy.context.scene.objects:
    R['objects'].append([o.name, o.type, o.parent.name if o.parent else None, [round(v, 4) for v in o.matrix_world.translation], [round(v, 4) for v in o.scale], [round(math.degrees(a), 1) for a in o.rotation_euler]])
for o in bpy.context.scene.objects:
    if o.type == 'ARMATURE':
        bones = {}
        for b in o.data.bones:
            h = o.matrix_world @ b.head_local; t = o.matrix_world @ b.tail_local
            bones[b.name] = dict(parent=b.parent.name if b.parent else None, head=[round(v, 4) for v in h], tail=[round(v, 4) for v in t])
        R['armatures'][o.name] = dict(n=len(bones), bones=bones)
    if o.type == 'MESH':
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
        R['meshes'][o.name] = dict(verts=len(o.data.vertices), faces=len(o.data.polygons), groups=len(o.vertex_groups), shape_keys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
                                   materials=[m.name if m else None for m in o.data.materials], bbox_min=[round(v, 4) for v in mn], bbox_max=[round(v, 4) for v in mx], modifiers=[m.type for m in o.modifiers], parent=o.parent.name if o.parent else None)
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('SAORI_INSPECT', len(R['armatures']), len(R['meshes']))
