"""PIE: 권총 장착 후 1발 -> 프레임마다 슬라이드 상대 X / SlideCur 기록 (후퇴 후 복귀 확인).  -> Saved/Scratch/p200_slide.json"""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_slide.json'
R = {'samples': [], 'timer_info': {}}; S = {'stage': 0, 't0': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; S['t0'] = now; S['stage'] = 1; return
        p = S['p']
        if S['stage'] == 1 and now - S['t0'] > 1.0:
            p.call_method('FurinaSwapMid'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and now - S['t0'] > 0.8:
            sl = p.get_editor_property('FurinaPistolSlide'); R['before'] = round(sl.relative_location.x, 3)
            R['timer_active'] = unreal.SystemLibrary.k2_is_timer_active(p, 'FurinaP200Tick') if hasattr(unreal.SystemLibrary, 'k2_is_timer_active') else 'n/a'
            p.call_method('FurinaRifleShot'); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3:
            sl = p.get_editor_property('FurinaPistolSlide'); R['samples'].append([round(now - S['t0'], 3), round(sl.relative_location.x, 3), round(float(p.get_editor_property('FurinaSlideCur')), 3)])
            if now - S['t0'] > 0.6:
                S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_SLIDE done')
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
S['h'] = unreal.register_slate_post_tick_callback(tick); les.editor_request_begin_play(); save(); print('P200_SLIDE armed')
