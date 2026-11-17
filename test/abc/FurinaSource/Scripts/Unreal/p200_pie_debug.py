"""PIE 디버그: PistolFx / P200Tick 이벤트를 직접 호출하며 슬라이드 위치 변화 확인. -> Saved/Scratch/p200_debug.json"""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_debug.json'
R = {'rows': []}; S = {'stage': 0, 't0': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; S['t0'] = now; S['stage'] = 1; return
        p = S['p']; sl = p.get_editor_property('FurinaPistolSlide')
        def row(tag): R['rows'].append([tag, round(float(p.get_editor_property('FurinaSlideCurF')), 3), round(sl.relative_location.x, 3)])
        if S['stage'] == 1 and now - S['t0'] > 1.0:
            row('start'); p.call_method('FurinaPistolFx'); row('after Fx call'); p.call_method('FurinaP200Tick'); row('after Tick call 1'); p.call_method('FurinaP200Tick'); row('after Tick call 2')
            S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2:
            row('free run %.3f' % (now - S['t0']))
            if now - S['t0'] > 0.5:
                S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h']); print('P200_DEBUG done')
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P200_DEBUG armed')

