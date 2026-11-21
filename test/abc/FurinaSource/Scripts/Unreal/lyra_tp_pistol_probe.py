"""Lyra 에디터(`py <파일> [태그]`): 3인칭 권총(FurinaSwapMid) 대기/걷기/달리기 자세를 여러 각도에서 캡처.
 캡처: Data/tppist_<태그>_<상태>_<각도번호>.png   기록: Data/lyra_tp_pistol_probe_<태그>.json
 상태: idle(4각도: 뒤/오른쪽/왼쪽/앞), walk(오른쪽, 앞), run(오른쪽, 앞)  - 걷기/달리기는 이동 입력(0.5/1.0)"""
import unreal, json, sys, time, math, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_tp_pistol_probe_%s.json' % TAG
SEQ = [('idle', 0, 0.0, 0), ('idle', 1, 0.0, -90), ('idle', 2, 0.0, 90), ('idle', 3, 0.0, 180), ('walk', 0, 0.5, -90), ('walk', 1, 0.5, 180), ('run', 0, 1.0, -90), ('run', 1, 1.0, 180), ('run', 2, 1.0, 0)]
R = {'tag': TAG, 'shots': []}; S = {'st': 'open', 't': 0, 'i': 0, 'sub': 0}
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
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 120
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st not in ('ending', 'done') and p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'; S['t'] = now
            return
        if st == 'settle' and now >= S['t']:
            n_d = 0
            for ac in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn):
                if ac != p and ('Mannequin' in ac.get_class().get_name() or 'Manny' in ac.get_class().get_name() or 'Quinn' in ac.get_class().get_name()): ac.k2_destroy_actor(); n_d += 1
            R['destroyed'] = n_d
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            S['yaw0'] = p.get_actor_rotation().yaw; S['st'] = 'seq'; S['t'] = now + 0.5; S['sub'] = 0; return
        if st == 'seq':
            state, k, move, yo = SEQ[S['i']]
            yaw0 = S['yaw0']; fwd = unreal.Vector(math.cos(math.radians(yaw0)), math.sin(math.radians(yaw0)), 0)
            if move > 0: p.add_movement_input(fwd, move, False)
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw0 + yo))
            if now < S['t']: return
            if S['sub'] == 0: S['sub'] = 1; S['t'] = now + (1.6 if move > 0 else 1.2); return
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/tppist_%s_%s_%d.png"' % (D, TAG, state, k)); R['shots'].append([state, k, move, yo])
            S['i'] += 1; S['sub'] = 0; S['t'] = now + 0.6
            if S['i'] >= len(SEQ): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_TP_PISTOL_PROBE armed', TAG)
