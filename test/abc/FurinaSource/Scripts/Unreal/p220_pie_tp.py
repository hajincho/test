"""PIE 3인칭 옆면 캡처: 소총 기본 / 권총(몽타주 없음) / 권총 대기 몽타주 / 재장전 몽타주 / 장착 몽타주."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_tp.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0}
A = '/Game/Furina/P220/Anim/'
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
def play(p, seq, loops=1, blend=0.2):
    inst = p.get_editor_property('FurinaMesh').get_anim_instance()
    inst.play_slot_animation_as_dynamic_montage(unreal.load_asset(A + seq), 'DefaultSlot', blend, blend, 1.0, loops, -1.0, 0.0)
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
            yaw = p.get_actor_rotation().yaw; pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=yaw - 80)); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 1.8: shot(w, '1_rifle_side'); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 1.5: shot(w, '2_pistol_nomontage'); play(p, 'Furina_Pistol_Idle_Hipfire', 9999); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 1.2: shot(w, '3_pistol_hold'); play(p, 'Furina_Pistol_Reload'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and el > 0.9: shot(w, '4_pistol_reload_mid'); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and el > 2.0: S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P220_TP armed')
