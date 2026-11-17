"""PIE: 리타게팅한 Lyra 권총 시퀀스를 DefaultSlot 동적 몽타주로 재생해 1인칭/3인칭 캡처.  -> Saved/Scratch/p220_anim.json"""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_anim.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0}
A = '/Game/Furina/P220/Anim/'
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
def play(p, seq, loops=1):
    inst = p.get_editor_property('FurinaMesh').get_anim_instance()
    m = inst.play_slot_animation_as_dynamic_montage(unreal.load_asset(A + seq), 'DefaultSlot', 0.2, 0.2, 1.0, loops, -1.0, 0.0)
    R.setdefault('played', []).append([seq, str(m)[:60]])
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(True); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; el = now - S['t0']
        if S['stage'] == 1 and el > 2.0: p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 1.0: play(p, 'Furina_Pistol_Idle_Hipfire', 9999); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 1.2: shot(w, '1_FP_hold'); play(p, 'Furina_Pistol_Equip'); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 0.7: shot(w, '2_FP_equip_mid'); play(p, 'Furina_Pistol_Reload'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and el > 0.9: shot(w, '3_FP_reload_mid'); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and el > 1.6:
            p.get_editor_property('FurinaFPWanted').set_active(False); play(p, 'Furina_Pistol_Idle_Hipfire', 9999); S['t0'] = now; S['stage'] = 7
        elif S['stage'] == 7 and el > 2.5: shot(w, '4_TP_hold'); S['t0'] = now; S['stage'] = 8
        elif S['stage'] == 8 and el > 0.8:
            S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P220_ANIM armed')
