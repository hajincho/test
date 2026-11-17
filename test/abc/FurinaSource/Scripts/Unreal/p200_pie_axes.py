"""PIE 실험: 타이머를 멈추고 소총 소켓 상대 오프셋 축(±X/Y/Z, 피치)을 바꿔가며 캡처해 '아래로 빠지는' 축을 찾는다."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_axes.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0, 'i': 0}
POSES = [('base', 0, 0, 0, 0), ('X-14', -14, 0, 0, 0), ('X+14', 14, 0, 0, 0), ('Y-14', 0, -14, 0, 0), ('Y+14', 0, 14, 0, 0), ('Z+14', 0, 0, 14, 0), ('Z-14', 0, 0, -14, 0), ('P-40', 0, 0, 0, -40), ('P+40', 0, 0, 0, 40)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(True); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; rifle = p.get_editor_property('FurinaRifle')
        if S['stage'] == 1 and now - S['t0'] > 2.0:
            p.call_method('FurinaSwapMid'); unreal.SystemLibrary.clear_timer(p, 'FurinaP200Tick')
            loc = rifle.relative_location; rot = rifle.relative_rotation; S['base'] = (loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and now - S['t0'] > 1.2:
            name, dx, dy, dz, dp = POSES[S['i']]; b = S['base']
            rifle.set_relative_location(unreal.Vector(b[0] + dx, b[1] + dy, b[2] + dz), False, False)
            rifle.set_relative_rotation(unreal.Rotator(roll=b[5], pitch=b[3] + dp, yaw=b[4]), False, False); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and now - S['t0'] > 0.7:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(POSES[S['i']][0]); S['i'] += 1; S['t0'] = now
            S['stage'] = 2 if S['i'] < len(POSES) else 4
        elif S['stage'] == 4 and now - S['t0'] > 1.0:
            S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_AXES done')
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P200_AXES armed')

