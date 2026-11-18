"""Lyra PIE(Play 전에 무장, 이후 손대지 않기): 3인칭 '사격 자세'(FireHold) 점검. 잔탄을 0으로 만들고 FurinaRifleShot 을 0.7초마다 호출해(사용자 팁: 0발에서 좌클릭 = 반동 없는 깔끔한 사격 자세)
자세를 유지한 채, 카메라 피치 -5도로 두고 폰을 -90/+90/180/0 도 돌려 HighResShot 2 -> Data/fire_<태그>_<각도>.png,
개머리판 끝/중간, 오른쪽 어깨 관절(Right-arm)/쇄골(Right-shoulder), 가슴/척추, 양손목 위치를 폰 로컬(x 앞, y 오른쪽, z 위) 로 기록 -> Data/lyra_fire_pose_<태그>.json
사용: py "<파일>" <태그>(기본 run)"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'run'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D + r'\lyra_fire_pose_%s.json' % TAG
R = {'tag': TAG, 'shots': []}; S = {'st': 0, 't': 0, 'last': 0, 'i': 0, 'base': None}
YAWS = [0.0, -90.0, 90.0]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def measure(p):
    comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
    mesh = comps['FurinaMesh']; rifle = comps['FurinaRifle']; pt = p.get_actor_transform()
    def loc(wv): t = unreal.MathLibrary.inverse_transform_location(pt, wv); return [round(t.x, 1), round(t.y, 1), round(t.z, 1)]
    gt = rifle.get_world_transform(); row = {}
    for nm, lv in (('butt', (0, -39.37, 4.53)), ('butt_top', (0, -39.37, 9.0)), ('butt_bot', (0, -39.37, -2.0)), ('stock_mid', (0, -30.0, 3.0)), ('receiver', (0, -5.0, 3.0)), ('muzzle', (0, 40.5, 3.4))):
        row[nm] = loc(unreal.MathLibrary.transform_location(gt, unreal.Vector(*lv)))
    for b in ('Hips', 'Spine', 'Chest', 'Neck', 'Head', 'Right-shoulder', 'Right-arm', 'Right-elbow', 'Right-wrist', 'Left-shoulder', 'Left-arm', 'Left-elbow', 'Left-wrist'):
        row[b] = loc(mesh.get_socket_location(b))
    li = unreal.MathLibrary.inverse_transform_location(gt, mesh.get_socket_location('Left-wrist')); row['Lwrist_in_rifle'] = [round(li.x, 2), round(li.y, 2), round(li.z, 2)]   # 정상(3인칭): 약 (3.2, 3.0, 2.0)
    row['L_reach'] = round((mesh.get_socket_location('Left-arm') - mesh.get_socket_location('Left-wrist')).length(), 2)
    row['L_clav'] = round((mesh.get_socket_location('Left-shoulder') - mesh.get_socket_location('Left-arm')).length(), 2)
    row['R_clav'] = round((mesh.get_socket_location('Right-shoulder') - mesh.get_socket_location('Right-arm')).length(), 2)
    for cv in ('FireHold', 'AimShoulder', 'AimADS', 'ViewTP'):
        try: row['curve_' + cv] = round(mesh.get_anim_instance().get_curve_value(cv), 3)
        except Exception: pass
    return row
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        if S['st'] >= 1:
            # FurinaAmmo 는 인스턴스에서 쓸 수 없어서, 잔탄이 0이 될 때까지 매 틱 사격 이벤트를 불러 비운 뒤(사격 간격은 BP 가 관리) 0.7초마다 계속 호출해 FireHold 를 유지
            try:
                ammo = p.get_editor_property('FurinaAmmo')
                if ammo > 0 or now - S['last'] > 0.7: p.call_method('FurinaRifleShot'); S['last'] = now
                R['ammo'] = ammo
            except Exception as e: R['shot_err'] = str(e)[:120]
        if S['st'] == 0:
            p.get_editor_property('FurinaFPWanted').set_active(False); S['base'] = p.get_actor_rotation().yaw; S['st'] = 1; S['t'] = now + 8
            # 봇이 카메라와 캐릭터 사이를 가려서, 빈 바닥 쪽으로 옆으로 6m 옮긴다(측정은 폰 로컬이라 영향 없음)
            p.set_actor_location(p.get_actor_location() + unreal.Vector(0, 600, 0), False, True)
            pc = unreal.GameplayStatics.get_player_controller(w, 0); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=(35 if 'up' in TAG else (-30 if 'down' in TAG else -5)), yaw=S['base']))   # 태그에 up/down 이 있으면 위/아래 조준
        elif S['st'] == 1 and now >= S['t'] and R.get('ammo', 1) == 0:
            R['pose'] = measure(p); save()
            p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['base'] + YAWS[S['i']]), False); S['st'] = 2; S['t'] = now + 2.0
        elif S['st'] == 2 and now >= S['t']:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s\\fire_%s_%d.png"' % (D, TAG, int(YAWS[S['i']]))); R['shots'].append(YAWS[S['i']]); save()
            S['i'] += 1
            if S['i'] >= len(YAWS): R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h']); return
            p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['base'] + YAWS[S['i']]), False); S['t'] = now + 2.0
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FIRE_POSE armed', TAG)
