"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 3인칭에서 소총 상태(허리 홀스터 권총)와 권총 상태(등 맨 소총)를 여러 각도(뒤/오른쪽/왼쪽/앞)에서 캡처.
 캡처: Data/tpgear_<태그>_<rifle|pistol>_<번호>.png   기록: Data/lyra_tp_gear_probe_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_tp_gear_probe_%s.json' % TAG
R = {'tag': TAG, 'shots': []}; S = {'st': 'open', 't': 0, 'vi': 0, 'phase': 'rifle'}
YAWS = [0, -90, 90, 180]
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
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            R['comps'] = [[n, comp(p, n) is not None] for n in ('FurinaSlingM4', 'FurinaHolsterFrame', 'FurinaHolsterSlide')]
            for n in ('FurinaSlingM4', 'FurinaHolsterFrame'):
                c = comp(p, n)
                if c is not None: R[n] = {'vis': bool(c.is_visible()), 'parent': c.get_attach_parent().get_name() if c.get_attach_parent() else None, 'socket': str(c.get_attach_socket_name())}
            S['st'] = 'view'; S['t'] = now + 1; S['vi'] = 0; S['sub'] = 0; save(); return
        if st == 'view' and now >= S['t']:
            yaw0 = p.get_actor_rotation().yaw
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=yaw0 + YAWS[S['vi']]))
            if S['sub'] == 0: S['sub'] = 1; S['t'] = now + 1.0; return
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/tpgear_%s_%s_%d.png"' % (D, TAG, S['phase'], S['vi'])); R['shots'].append([S['phase'], S['vi']])
            S['vi'] += 1; S['sub'] = 0; S['t'] = now + 1.2
            if S['vi'] >= len(YAWS):
                if S['phase'] == 'rifle': p.call_method('FurinaSwapMid'); S['phase'] = 'pistol'; S['vi'] = 0; S['t'] = now + 3
                else: S['st'] = 'end'; S['t'] = now + 1
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_TP_GEAR_PROBE armed', TAG)
