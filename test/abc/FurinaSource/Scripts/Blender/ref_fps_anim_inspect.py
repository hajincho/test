"""blender -b --python ref_fps_anim_inspect.py -- <fbx> <out.json> : 참고용 1인칭 애니 FBX 조사(액션 목록/프레임 범위/뼈 계층/메시) — 동작 참고만, 직접 쓰지 않음"""
import bpy, sys, json
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=A[0], use_anim=True)
sc = bpy.context.scene; R = {'fps': sc.render.fps, 'objects': [], 'actions': []}
for o in bpy.data.objects:
    e = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None, 'dims_cm': [round(d * 100, 1) for d in o.dimensions]}
    if o.type == 'ARMATURE': e['bones'] = [[b.name, b.parent.name if b.parent else None] for b in o.data.bones]
    if o.type == 'MESH': e['verts'] = len(o.data.vertices); e['vgroups'] = len(o.vertex_groups); e['mats'] = [m.name for m in o.data.materials if m]
    if o.animation_data and o.animation_data.action: e['action'] = o.animation_data.action.name
    R['objects'].append(e)
for a in bpy.data.actions:
    fr = a.frame_range; R['actions'].append({'name': a.name, 'range': [round(fr[0], 1), round(fr[1], 1)], 'sec': round((fr[1] - fr[0]) / sc.render.fps, 2)})
for m in bpy.data.objects:
    if m.type == 'ARMATURE' and m.animation_data and m.animation_data.nla_tracks:
        R['nla'] = [[t.name, [[s.name, s.action.name if s.action else None, s.frame_start, s.frame_end] for s in t.strips]] for t in m.animation_data.nla_tracks]
json.dump(R, open(A[1], 'w'), indent=1); print('REF_OK', len(R['actions']), [a['name'] for a in R['actions']])
