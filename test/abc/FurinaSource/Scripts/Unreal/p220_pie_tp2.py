"""PIE 3인칭 옆면: 권총 장착(Equip) -> 대기(Hold) -> 재장전 -> 사격 -> 소총 복귀. 전환 시점마다 캡처."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_tp2.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
STEPS = []
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(False); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; el = now - S['t0']; pc = unreal.GameplayStatics.get_player_controller(w, 0)
        if S['stage'] == 1 and el > 2.5:
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=p.get_actor_rotation().yaw - 80)); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 1.8: p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 0.7: shot(w, '1_equip_mid'); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 2.0: shot(w, '2_hold'); p.call_method('FurinaRequestReload'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and el > 1.0: shot(w, '3_reload_mid'); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and el > 2.5: shot(w, '4_after_reload_hold'); p.call_method('FurinaRifleShot'); S['t0'] = now; S['stage'] = 7
        elif S['stage'] == 7 and el > 0.15: shot(w, '5_fire'); S['t0'] = now; S['stage'] = 8
        elif S['stage'] == 8 and el > 1.5: p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 9
        elif S['stage'] == 9 and el > 1.2: shot(w, '6_back_to_rifle'); S['t0'] = now; S['stage'] = 10
        elif S['stage'] == 10 and el > 1.0:
            S['stage'] = 99; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P220_TP2 armed')
