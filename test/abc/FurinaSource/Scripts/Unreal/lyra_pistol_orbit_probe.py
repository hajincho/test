"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 포즈(FPCamera 활성 -> CR 이 1인칭 파지 계산)를 유지한 채 3인칭 카메라(FollowCamera 활성)와 스프링암을 짧게 줄여 손/총을 여러 방향에서 찍는다.
 먼저 카메라/스프링암 컴포넌트 목록과 활성 상태를 기록하고, 두 카메라를 모두 활성으로 둔 상태에서 실제 화면이 어느 쪽인지 캡처로 확인.
 캡처: Data/orbit_<태그>_<번호>.png   기록: Data/lyra_pistol_orbit_probe_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_pistol_orbit_probe_%s.json' % TAG
R = {'tag': TAG, 'shots': [], 'comps': []}; S = {'st': 'open', 't': 0, 'vi': 0}
# (yaw 오프셋(폰 기준), pitch, 팔 길이, 소켓 오프셋)  - 오른쪽 손/총 부근을 여러 각도에서
VIEWS = [(-90, -10, 55), (90, -10, 55), (180, -10, 55), (0, -10, 55), (-90, -60, 55), (-135, -20, 55)]
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
            p.get_editor_property('FurinaFPWanted').set_active(True)
            for c in p.get_components_by_class(unreal.CameraComponent): R['comps'].append(['cam', c.get_name(), bool(c.is_active()), str(c.get_attach_parent().get_name()) if c.get_attach_parent() else None])
            for c in p.get_components_by_class(unreal.SpringArmComponent): R['comps'].append(['arm', c.get_name(), bool(c.is_active()), float(c.target_arm_length)])
            save(); S['st'] = 'dual'; S['t'] = now + 2; return
        if st == 'dual' and now >= S['t']:
            for c in p.get_components_by_class(unreal.CameraComponent):
                if c.get_name() != 'FPCamera': c.set_active(True)
            R['after_dual'] = [[c.get_name(), bool(c.is_active())] for c in p.get_components_by_class(unreal.CameraComponent)]
            S['st'] = 'view'; S['t'] = now + 1.5; S['vi'] = 0; S['sub'] = 0; save(); return
        if st == 'view' and now >= S['t']:
            yaw0 = p.get_actor_rotation().yaw; yo, pi, ln = VIEWS[S['vi']]
            for a in p.get_components_by_class(unreal.SpringArmComponent):
                a.set_editor_property('target_arm_length', float(ln)); a.set_editor_property('do_collision_test', False)
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pi, yaw=yaw0 + yo))
            if S['sub'] == 0: S['sub'] = 1; S['t'] = now + 1.0; return
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/orbit_%s_%02d.png"' % (D, TAG, S['vi'])); R['shots'].append(S['vi'])
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
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_ORBIT_PROBE armed', TAG)
