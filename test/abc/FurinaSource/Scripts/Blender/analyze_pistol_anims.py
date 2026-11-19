"""blender.exe -b --python analyze_pistol_anims.py : Armpist.fbx 의 액션별 숫자 요약 -> Data/pistol_anim_numbers.json
 매 프레임(60fps) 뼈 머리 위치(아마추어 로컬, m -> cm)를 샘플링해 구간 범위, 이동 거리, 시작-끝 차이, 최대 변위 시각, 속도, 회전 범위를 계산한다."""
import bpy, json, math
import mathutils
SRC = r'C:\Users\fromj\Downloads\fps-pistol-animations\source\Armpist.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pistol_anim_numbers.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = bpy.data.objects['Armature']; sc = bpy.context.scene; FPS = sc.render.fps
TR = ['Head_Cam', 'Hand_L', 'Hand_R', 'IK_Hand_Cntrl_L', 'IK_Hand_Cntrl_R', 'Forearm_L', 'Forearm_R', 'PBody', 'Rif', 'Trigger', 'Pmag', 'Root']
R = {'fps': FPS, 'unit': 'cm (FBX m x100), 축=아마추어 로컬', 'rest': {}, 'actions': {}}
if arm.animation_data is None: arm.animation_data_create()
# 레스트(포즈 없음) 위치
for b in TR:
    pb = arm.pose.bones.get(b)
    if pb: R['rest'][b] = [round(x * 100, 2) for x in (arm.matrix_world @ pb.bone.head_local)]
for act in bpy.data.actions:
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    fr0, fr1 = int(act.frame_range[0]), int(act.frame_range[1]); data = {b: [] for b in TR}; rot = {b: [] for b in ('PBody', 'Rif', 'Head_Cam', 'Hand_L', 'Hand_R')}
    for f in range(fr0, fr1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for b in TR:
            pb = arm.pose.bones.get(b)
            if pb: data[b].append([x * 100 for x in (arm.matrix_world @ pb.head)])
        for b in rot:
            pb = arm.pose.bones.get(b)
            if pb: rot[b].append([math.degrees(a) for a in (arm.matrix_world @ pb.matrix).to_euler()])
    A = {'frames': fr1 - fr0, 'seconds': round((fr1 - fr0) / FPS, 3), 'bones': {}}
    for b, pts in data.items():
        if not pts: continue
        n = len(pts); mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
        path = sum(math.dist(pts[i], pts[i + 1]) for i in range(n - 1)); st = pts[0]; en = pts[-1]
        disp = [math.dist(p, st) for p in pts]; im = max(range(n), key=lambda i: disp[i])
        vel = [math.dist(pts[i], pts[i + 1]) * FPS / 100 for i in range(n - 1)]   # m/s
        A['bones'][b] = {'start': [round(x, 2) for x in st], 'end': [round(x, 2) for x in en], 'range': [round(mx[i] - mn[i], 2) for i in range(3)], 'min': [round(x, 2) for x in mn], 'max': [round(x, 2) for x in mx],
                         'path_cm': round(path, 2), 'start_end_gap_cm': round(math.dist(st, en), 2), 'max_disp_from_start_cm': round(disp[im], 2), 'frame_of_max': im, 'time_of_max_s': round(im / FPS, 3),
                         'peak_speed_m_s': round(max(vel), 2) if vel else 0, 'disp_series_every_5': [round(d, 2) for d in disp[::5]]}
    A['rot_range_deg'] = {b: [round(max(r[i] for r in v) - min(r[i] for r in v), 1) for i in range(3)] for b, v in rot.items() if v}
    R['actions'][act.name.split('|')[-1]] = A
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False); print('PISTOL_NUMBERS_OK', len(R['actions']))
