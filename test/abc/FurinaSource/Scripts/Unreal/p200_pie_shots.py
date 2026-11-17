"""PIE 스크린샷: 소총 / 권총 장착 / 스왑 하강 포즈를 캡처. -> Saved/Screenshots 의 HighResShot, 로그는 Saved/Scratch/p200_shots.json"""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_shots.json'
R = {'shots': []}; S = {'stage': 0, 't0': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def shot(w, name):
    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720'); R['shots'].append(name); save()
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; p.get_editor_property('FurinaFPWanted').set_active(True); S['t0'] = now; S['stage'] = 1; return
        p = S['p']; rifle = p.get_editor_property('FurinaRifle'); base_loc = rifle.relative_location; base_rot = rifle.relative_rotation
        if S['stage'] == 1 and now - S['t0'] > 2.5: shot(w, '1_rifle'); p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and now - S['t0'] > 1.5: shot(w, '2_pistol'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and now - S['t0'] > 1.0:
            p.set_editor_property('FurinaSwapTargetF', 1.0); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and now - S['t0'] > 1.2:
            shot(w, '3_swap_down'); R['swapcur'] = float(p.get_editor_property('FurinaSwapCurF')); R['rifle_rel'] = [rifle.relative_location.x, rifle.relative_location.y, rifle.relative_location.z, rifle.relative_rotation.pitch]
            p.set_editor_property('FurinaSwapTargetF', 0.0); S['t0'] = now; S['stage'] = 6
        elif S['stage'] == 6 and now - S['t0'] > 1.0:
            S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_SHOTS done')
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P200_SHOTS armed')



