"""blender -b --python ref_fps_anim_phases.py -- <fbx> <out.json> : 참고 애니의 볼트/손 궤적을 총(Body 뼈) 기준으로 프레임별 추출 + 단계 시점 추정
 볼트: Body 기준 Bolt 뼈의 이동(앞뒤)과 회전(총열 축 둘레) / 손: Hand_R, Hand_L 위치. 참고만 하며 그대로 쓰지 않음."""
import bpy, sys, json, math
from mathutils import Matrix
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=A[0], use_anim=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; R = {'fps': sc.render.fps, 'clips': {}}
pb = rig.pose.bones
for act in [a for a in bpy.data.actions if a.name.startswith('Rig|Rig|SRifle')]:
    rig.animation_data.action = act
    try: rig.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); rows = []
    body0 = None
    for f in range(f0, f1 + 1):
        sc.frame_set(f); M = rig.matrix_world
        B = M @ pb['Body'].matrix; Bi = B.inverted()
        bolt = Bi @ (M @ pb['Bolt'].matrix); hr = Bi @ (M @ pb['Hand_R'].matrix); hl = Bi @ (M @ pb['Hand_L'].matrix)
        if body0 is None: body0 = B.copy()
        cam = None
        rows.append({'f': f, 'bolt_t': [round(v * 100, 2) for v in bolt.translation], 'bolt_e': [round(math.degrees(v), 1) for v in bolt.to_euler()],
                     'hr': [round(v * 100, 2) for v in hr.translation], 'hl': [round(v * 100, 2) for v in hl.translation],
                     'body_t': [round(v * 100, 2) for v in (body0.inverted() @ B).translation], 'body_e': [round(math.degrees(v), 1) for v in (body0.inverted() @ B).to_euler()]})
    R['clips'][act.name.split('|')[-1]] = rows
json.dump(R, open(A[1], 'w'), indent=0); print('PHASES_OK', list(R['clips']))
