"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 권총 파지 근접 촬영. PIE 에서 권총 장착 + 1인칭 상태로 두고, 게임 월드에 카메라 액터를 만들어 소총 컴포넌트 기준 여러 방향(오른쪽/왼쪽/뒤/위/앞)에서
 손잡이 부근(소총 기준 (0,-11,-4))을 가까이서 찍는다.  기록: 뼈 위치(소총 기준), 프레임/슬라이드 경계.
 캡처: Data/closeup_<태그>_<방향>.png   기록: Data/lyra_pistol_hand_closeup_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_pistol_hand_closeup_%s.json' % TAG
R = {'tag': TAG, 'shots': []}; S = {'st': 'open', 't': 0, 'vi': 0}
TARGET = (0.0, -11.0, -4.0)
VIEWS = [('right', (-32.0, -11.0, -4.0)), ('left', (32.0, -11.0, -4.0)), ('rear', (0.0, -45.0, -3.0)), ('top', (0.0, -11.0, 34.0)), ('front', (0.0, 25.0, -3.0)), ('rear_right', (-24.0, -36.0, 6.0))]
BONES = ['Right-wrist', 'Left-wrist', 'Thumb0_R', 'Thumb1_R', 'Thumb2_R', 'IndexFinger1_R', 'IndexFinger3_R', 'MiddleFinger1_R', 'MiddleFinger3_R', 'RingFinger3_R', 'LittleFinger3_R', 'Thumb2_L', 'IndexFinger3_L', 'MiddleFinger3_L', 'LittleFinger3_L']
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st not in ('ending', 'done') and p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 9
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 'fp'; S['t'] = now + 2.5; return
        if st == 'fp' and now >= S['t']:
            cam = comp(p, 'FPCamera'); cam.set_absolute(True, True, False)
            cam.set_editor_property('field_of_view', 55.0); S['cam'] = cam; R['cam'] = str(cam); S['st'] = 'view'; S['t'] = now; S['vi'] = 0; S['sub'] = 0; return
        if st == 'view' and now >= S['t']:
            rifle = comp(p, 'FurinaRifle'); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); tf = rifle.get_world_transform()
            name, off = VIEWS[S['vi']]
            cam_loc = tf.transform_location(unreal.Vector(*off)); tgt = tf.transform_location(unreal.Vector(*TARGET))
            rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, tgt)
            S['cam'].set_world_location_and_rotation(cam_loc, rot, False, True)
            if S['sub'] == 0:
                S['sub'] = 1; S['t'] = now + 0.8; return
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/closeup_%s_%s.png"' % (D, TAG, name)); R['shots'].append(name)
            if S['vi'] == 0:
                inv = tf.inverse()
                def g(v): q = inv.transform_location(v); return [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
                R['bones'] = {b: g(mesh.get_socket_location(b)) for b in BONES}
                frame = comp(p, 'FurinaPistolFrame', unreal.StaticMeshComponent); bb = frame.static_mesh.get_bounding_box(); ctf = frame.get_world_transform(); pts = []
                for x in (bb.min.x, bb.max.x):
                    for y in (bb.min.y, bb.max.y):
                        for z in (bb.min.z, bb.max.z): pts.append(g(ctf.transform_location(unreal.Vector(x, y, z))))
                R['frame_min'] = [min(q[i] for q in pts) for i in range(3)]; R['frame_max'] = [max(q[i] for q in pts) for i in range(3)]; save()
            S['vi'] += 1; S['sub'] = 0; S['t'] = now + 1.2
            if S['vi'] >= len(VIEWS): S['st'] = 'end'; S['t'] = now + 1.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_HAND_CLOSEUP armed', TAG)
