"""PIE(1인칭): 권총 프레임 상대 위치 후보를 바꿔가며 캡처. 컴포넌트 값만 변경(그래프 편집 없음)."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_place.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0, 'i': 0}
BASE = (0.0, -4.27, 0.63)
POSES = [('base', 0, 0, 0, 0), ('fwd6', 0, 6, 0, 0), ('fwd10_dn2', 0, 10, -2, 0), ('fwd8_left3', 3, 8, 0, 0), ('fwd8_right3', -3, 8, 0, 0), ('fwd8_up2', 0, 8, 2, 0), ('fwd8_yaw+8', 0, 8, 0, 8), ('fwd8_yaw-8', 0, 8, 0, -8)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(True); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; fr = p.get_editor_property('FurinaPistolFrame')
        if S['stage'] == 1 and now - S['t0'] > 2.0: p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and now - S['t0'] > 1.0:
            n, dx, dy, dz, dyaw = POSES[S['i']]
            fr.set_relative_location(unreal.Vector(BASE[0] + dx, BASE[1] + dy, BASE[2] + dz), False, False)
            fr.set_relative_rotation(unreal.Rotator(roll=0, pitch=0, yaw=90 + dyaw), False, False); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and now - S['t0'] > 0.6:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(POSES[S['i']][0]); S['i'] += 1; S['t0'] = now
            S['stage'] = 2 if S['i'] < len(POSES) else 4
        elif S['stage'] == 4 and now - S['t0'] > 1.0:
            S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P200_PLACE armed')
