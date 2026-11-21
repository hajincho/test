"""blender -b --python fp_arms_inspect.py : Furina_cm.fbx 구조(오브젝트/머티리얼/팔 가중치 정점 수) 확인 -> Data/fp_arms_inspect.json"""
import bpy, json
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=D + r'\FBX\Furina_cm.fbx', automatic_bone_orientation=False, ignore_leaf_bones=False)
R = {'objects': []}
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
R['arm'] = {'name': arm.name, 'mw': [list(r) for r in arm.matrix_world], 'nbones': len(arm.data.bones)}
def desc(b):
    out = [b.name]
    for c in b.children: out += desc(c)
    return out
SETS = {s: set(desc(arm.data.bones['%s arm' % s])) for s in ('Left', 'Right')}
R['arm_bones'] = {k: sorted(v) for k, v in SETS.items()}
for o in bpy.data.objects:
    e = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None, 'mw': [list(r) for r in o.matrix_world]}
    if o.type == 'MESH':
        me = o.data; e['nv'] = len(me.vertices); e['nf'] = len(me.polygons); e['mats'] = [m.name if m else None for m in me.materials]
        e['has_custom_normals'] = bool(getattr(me, 'has_custom_normals', False)); e['attrs'] = [(a.name, a.domain, a.data_type) for a in me.attributes]
        e['uv'] = [u.name for u in me.uv_layers]
        gi = {g.index: g.name for g in o.vertex_groups}
        for side, bs in SETS.items():
            cnt = 0; mats = {}
            for v in me.vertices:
                wsum = sum(g.weight for g in v.groups if gi.get(g.group) in bs)
                if wsum >= 0.5: cnt += 1
            e['arm_%s' % side] = cnt
        e['mods'] = [(m.type, m.name) for m in o.modifiers]
    R['objects'].append(e)
json.dump(R, open(D + r'\Data\fp_arms_inspect.json', 'w'), indent=1)
print('INSPECT_OK')
