"""PIE 3인칭 옆면: 권총 후보 자세 비교 (Idle_Hipfire / Idle_ADS / Equip 끝 / Crouch_Idle). 슬롯 몽타주로 재생해 캡처."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_poses.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0}
A = '/Game/Furina/P220/Anim/'
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
def play(p, seq, loops=9999):
    inst = p.get_editor_property('FurinaMesh').get_anim_instance(); inst.play_slot_animation_as_dynamic_montage(unreal.load_asset(A + seq), 'DefaultSlot', 0.15, 0.15, 1.0, loops, -1.0, 0.0)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(False); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; el = now - S['t0']; pc = unreal.GameplayStatics.get_player_controller(w, 0)
        if S['stage'] == 1 and el > 3.0:
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=p.get_actor_rotation().yaw + 150)); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 3.5: play(p, 'Furina_Pistol_Idle_Hipfire'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 1.5: shot(w, '1_MM_Idle_Hipfire'); play(p, 'MF_Pistol_Idle_Hipfire'); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 1.5: shot(w, '2_MF_Idle_Hipfire'); play(p, 'MF_Pistol_Idle_ADS'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and el > 1.3: shot(w, '3_MF_Idle_ADS'); play(p, 'Furina_Pistol_Idle_ADS'); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and el > 0.7: shot(w, '4_MM_Idle_ADS'); S['t0'] = now; S['stage'] = 7
        elif S['stage'] == 7 and el > 1.5:
            S['stage'] = 99; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if 'FiringRange' not in str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()): R['load'] = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
S['h'] = unreal.register_slate_post_tick_callback(tick); les.editor_request_begin_play(); save(); print('P220_POSES armed')


