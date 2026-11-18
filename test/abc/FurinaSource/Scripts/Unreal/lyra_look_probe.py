"""Lyra 에디터(`py <파일> <경험이름> <맵경로>`, PIE 중지 상태): 경험 오버라이드를 바꾸고 맵을 연 뒤 PIE 를 직접 시작하고, 폰이 생기면 0.25초마다 최대 40초
(컨트롤 회전, RMB/LMB/V 눌림, FurinaADS/FPWanted/FPCamera 활성, 입력 무시 여부, 위젯/마우스 커서 표시, 입력 모드)를 기록한다. 이 동안 마우스를 움직이고 우클릭/V 를 눌러 본다.
끝나면 PIE 를 종료하고 경험 오버라이드를 B_Furina_Experience, 맵을 L_DefaultEditorOverview 로 되돌린다.  -> Data/lyra_look_probe.json"""
import unreal, json, sys, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_look_probe.json'
EXP = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].endswith('.py') else 'B_ShooterGame_Elimination'
MAP = sys.argv[2] if len(sys.argv) > 2 else '/ShooterMaps/Maps/L_Expanse_Blockout'
TRAVEL = sys.argv[3] if len(sys.argv) > 3 else None   # 예: /ShooterMaps/Maps/L_Expanse_Blockout?Experience=B_ShooterGame_Elimination  (PIE 시작 8초 뒤 ServerTravel)
R = {'exp': EXP, 'map': MAP, 'samples': []}; S = {'st': 'open', 't': 0, 'n': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(name):
    cdo = unreal.get_default_object(unreal.LyraDeveloperSettings); cdo.set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), name))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp(EXP); unreal.EditorLoadingAndSavingUtils.load_map(MAP); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play' and now >= S['t']:
            LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 120; return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if st == 'wait':
            p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
            if p is not None: S['st'] = 'rec'; S['t0'] = now; S['t'] = now; R['started'] = True
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'finish'
            return
        if st == 'rec':
            if now < S['t']: return
            S['t'] = now + 0.25
            p = unreal.GameplayStatics.get_player_pawn(w, 0); pc = unreal.GameplayStatics.get_player_controller(w, 0)
            if p is None or pc is None: return
            s = {'t': round(now - S['t0'], 2), 'world': w.get_name() if w else None}
            if TRAVEL and not S.get('tr') and now - S['t0'] > 8:
                S['tr'] = True; s['travel'] = TRAVEL
                if TRAVEL == 'portal':   # 첫 B_TeleportToUserFacingExperience 액터 위치로 폰을 순간이동(오버랩으로 포탈 작동)
                    ps = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if 'TeleportToUserFacing' in a.get_class().get_name()]
                    s['portals'] = [[a.get_name(), str(a.get_actor_location())] for a in ps][:8]
                    if ps: p.set_actor_location(ps[0].get_actor_location(), False, True)
                else: unreal.SystemLibrary.execute_console_command(w, 'ServerTravel ' + TRAVEL)
            rot = pc.get_control_rotation(); s['rot'] = [round(rot.pitch, 1), round(rot.yaw, 1)]
            for k in ('RightMouseButton', 'LeftMouseButton', 'V', 'MouseX', 'MouseY'):
                try: s[k] = bool(pc.is_input_key_down(unreal.Key(key_name=k))) if k[:5] != 'Mouse' else round(pc.get_input_analog_key_state(unreal.Key(key_name=k)), 2)
                except Exception as e: s[k + '_e'] = str(e)[:40]
            names = {'FurinaADS': 'ads', 'FurinaFPWanted': 'fpw', 'FurinaShoulder': 'sh', 'FurinaSpecial': 'sp'}
            for c in p.get_components_by_class(unreal.ActorComponent):
                if c.get_name() in names:
                    try: s[names[c.get_name()]] = bool(c.is_active())
                    except Exception: pass
            try: s['look_ign'] = pc.is_look_input_ignored(); s['move_ign'] = pc.is_move_input_ignored()
            except Exception: pass
            try: s['cursor'] = bool(pc.get_editor_property('show_mouse_cursor'))
            except Exception as e: s['cursor_e'] = str(e)[:40]
            R['samples'].append(s); S['n'] += 1
            if S['n'] % 8 == 0: save()
            if now - S['t0'] > (70 if TRAVEL else 40): S['st'] = 'finish'
            return
        if st == 'finish':
            save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); R['done'] = True; save(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_LOOK_PROBE armed', EXP, MAP)
