"""Blender: Downloads/m4-fps-weapon-animations-pack-v1/source/M4.fbx 구조 조사 (오브젝트, 아마추어/본, 액션과 프레임 범위, fps) -> FurinaSource/Data/m4_pack_inspect.json
사용: blender.exe -b --python inspect_m4_pack.py"""
import bpy, json
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\m4_pack_inspect.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\m4-fps-weapon-animations-pack-v1\source\M4.fbx', use_anim=True, anim_offset=0.0)
R = {'fps': bpy.context.scene.render.fps, 'fps_base': bpy.context.scene.render.fps_base, 'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end], 'objects': [], 'actions': {}}
for o in bpy.data.objects:
    row = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None, 'loc': [round(v, 3) for v in o.location], 'rot': [round(v, 3) for v in o.rotation_euler], 'scale': [round(v, 3) for v in o.scale]}
    if o.type == 'ARMATURE':
        row['bones'] = [[b.name, b.parent.name if b.parent else None] for b in o.data.bones]
        row['action'] = o.animation_data.action.name if o.animation_data and o.animation_data.action else None
    if o.type == 'MESH': row['verts'] = len(o.data.vertices); row['vgroups'] = len(o.vertex_groups)
    R['objects'].append(row)
for a in bpy.data.actions:
    R['actions'][a.name] = {'range': [round(a.frame_range[0], 2), round(a.frame_range[1], 2)], 'users': a.users, 'slots': [s.name_display for s in a.slots] if hasattr(a, 'slots') else None}
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('M4_INSPECT', len(R['objects']), len(R['actions']))
