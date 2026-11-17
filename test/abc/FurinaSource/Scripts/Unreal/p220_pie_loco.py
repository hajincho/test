"""PIE 3인칭 옆면: 권총 장착 후 대기 / 걷기 / 조깅 / 앉기 대기 / 앉아 걷기 / 소총 걷기 비교 캡처. 이동은 CharacterMovement.velocity 를 직접 설정."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_loco.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0, 'v': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(False); r = p.get_actor_rotation(); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=r.yaw + 90), False); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; el = now - S['t0']; pc = unreal.GameplayStatics.get_player_controller(w, 0)
        if S['v'] > 0:
            cm = p.get_editor_property('CharacterMovement'); f = p.get_actor_forward_vector(); cm.set_editor_property('velocity', unreal.Vector(f.x * S['v'], f.y * S['v'], 0.0))
            p.add_movement_input(f, 1.0, False)
        if S['stage'] == 1 and el > 3.0:
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=p.get_actor_rotation().yaw - 80)); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 3.0: shot(w, '1_idle_hold'); S['v'] = 150.0; S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 1.0: shot(w, '2_walk'); S['v'] = 500.0; S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 0.8: shot(w, '3_jog'); S['v'] = 0.0; p.call_method('FurinaToggleCrouch'); S['t0'] = now; S['stage'] = 5
        elif S['stage'] == 5 and el > 2.0: shot(w, '4_crouch_idle'); S['v'] = 100.0; S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and el > 1.5: shot(w, '5_crouch_walk'); S['v'] = 0.0; p.call_method('FurinaToggleCrouch'); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 7
        elif S['stage'] == 7 and el > 3.0: S['v'] = 150.0; S['t0'] = now; S['stage'] = 8
        elif S['stage'] == 8 and el > 1.5: shot(w, '6_rifle_walk'); S['v'] = 0.0; S['t0'] = now; S['stage'] = 9
        elif S['stage'] == 9 and el > 1.0:
            S['stage'] = 99; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if 'FiringRange' not in str(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()): R['load'] = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
S['h'] = unreal.register_slate_post_tick_callback(tick); les.editor_request_begin_play(); save(); print('P220_LOCO armed')


