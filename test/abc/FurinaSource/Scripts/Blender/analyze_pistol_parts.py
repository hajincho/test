"""blender.exe -b --python analyze_pistol_parts.py : Armpist.fbx 의 권총 부품 메시(프레임/슬라이드/탄창)를 매 프레임 스킨된 정점 무게중심으로 추적해 실제 부품 움직임 숫자를 낸다 -> Data/pistol_part_numbers.json
 단위 cm. 좌표계: 아마추어 월드(Z 위, 카메라 Head_Cam 은 고정). 슬라이드/탄창은 프레임 기준 상대 변위도 계산."""
import bpy, json, math
import numpy as np
SRC = r'C:\Users\fromj\Downloads\fps-pistol-animations\source\Armpist.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pistol_part_numbers.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = bpy.data.objects['Armature']; sc = bpy.context.scene; FPS = sc.render.fps
PARTS = {'frame': 'xd_frame', 'slide': 'xd_frame.001', 'mag': 'xd_frame.002', 'arms': 'arms'}
if arm.animation_data is None: arm.animation_data_create()
def cent(name):
    o = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); M = np.array(oe.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]; oe.to_mesh_clear(); return w
# 사양: 부품 정점 수와 정지 상태 경계(첫 액션 첫 프레임)
R = {'fps': FPS, 'unit': 'cm', 'parts_n': {}, 'actions': {}}
acts = [a for a in bpy.data.actions if not a.name.endswith(('.001', '.002'))]
for act in acts:
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); ser = {k: [] for k in ('frame', 'slide', 'mag')}; box = {k: [] for k in ('frame', 'slide', 'mag')}; hands = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for k in ser:
            w = cent(PARTS[k]) * 100; ser[k].append(w.mean(0)); box[k].append(np.concatenate([w.min(0), w.max(0)]))
        hands.append([np.array(arm.matrix_world @ arm.pose.bones[b].head) * 100 for b in ('Hand_L', 'Hand_R')])
    S = {k: np.array(v) for k, v in ser.items()}; H = np.array(hands)
    out = {'frames': f1 - f0, 'seconds': round((f1 - f0) / FPS, 3), 'parts': {}}
    for k in ('frame', 'slide', 'mag'):
        s = S[k]; d0 = np.linalg.norm(s - s[0], axis=1); im = int(d0.argmax())
        out['parts'][k] = {'start': [round(float(x), 2) for x in s[0]], 'end': [round(float(x), 2) for x in s[-1]], 'range': [round(float(x), 2) for x in (s.max(0) - s.min(0))], 'max_disp_cm': round(float(d0[im]), 2), 'frame_of_max': im, 'time_of_max_s': round(im / FPS, 3),
                           'end_gap_cm': round(float(np.linalg.norm(s[-1] - s[0])), 2), 'path_cm': round(float(np.linalg.norm(np.diff(s, axis=0), axis=1).sum()), 2), 'peak_speed_m_s': round(float(np.linalg.norm(np.diff(s, axis=0), axis=1).max() * FPS / 100), 2) if len(s) > 1 else 0}
    for k in ('slide', 'mag'):
        rel = S[k] - S['frame']; r0 = np.linalg.norm(rel - rel[0], axis=1); im = int(r0.argmax())
        out['parts'][k]['rel_to_frame'] = {'range': [round(float(x), 2) for x in (rel.max(0) - rel.min(0))], 'max_disp_cm': round(float(r0[im]), 2), 'frame_of_max': im, 'time_of_max_s': round(im / FPS, 3), 'series_every_3': [round(float(x), 2) for x in r0[::3]],
                                         'axis_of_travel': [round(float(x), 3) for x in ((rel[im] - rel[0]) / max(1e-6, np.linalg.norm(rel[im] - rel[0])))]}
    # 손: 프레임 무게중심 기준 상대 위치
    for i, nm in enumerate(('hand_L', 'hand_R')):
        rel = H[:, i] - S['frame']; r0 = np.linalg.norm(rel - rel[0], axis=1); im = int(r0.argmax())
        out['parts'][nm + '_rel_frame'] = {'start': [round(float(x), 2) for x in rel[0]], 'range': [round(float(x), 2) for x in (rel.max(0) - rel.min(0))], 'max_disp_cm': round(float(r0[im]), 2), 'time_of_max_s': round(im / FPS, 3),
                                           'path_cm': round(float(np.linalg.norm(np.diff(rel, axis=0), axis=1).sum()), 2), 'series_every_3': [round(float(x), 1) for x in r0[::3]]}
    R['actions'][act.name.split('|')[-1]] = out
R['parts_n'] = {k: len(bpy.data.objects[v].data.vertices) for k, v in PARTS.items()}
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('PARTS_OK', list(R['actions']))
