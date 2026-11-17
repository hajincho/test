"""PIE 디버그: SwapTargetF 를 1 로 올린 뒤 SwapCurF 와 소총 상대 위치 추적."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p200_debug2.json'
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
        p = S['p']; rifle = p.get_editor_property('FurinaRifle')
        def row(tag): R['rows'].append([tag, round(float(p.get_editor_property('FurinaSwapCurF')), 3), round(float(p.get_editor_property('FurinaSwapTargetF')), 3), [round(rifle.relative_location.x, 2), round(rifle.relative_location.y, 2), round(rifle.relative_location.z, 2)], unreal.SystemLibrary.is_timer_active(p, 'FurinaP200Tick')])
        if S['stage'] == 1 and now - S['t0'] > 1.5:
            row('before'); p.set_editor_property('FurinaSwapTargetF', 1.0); row('after set'); R['paused'] = unreal.SystemLibrary.is_timer_paused(p, 'FurinaP200Tick'); R['dilation'] = unreal.GameplayStatics.get_global_time_dilation(w); unreal.SystemLibrary.set_timer(p, 'FurinaP200Tick', 0.008, True); R['timer_elapsed'] = unreal.SystemLibrary.get_timer_elapsed_time(p, 'FurinaP200Tick'); R['timer_remaining'] = unreal.SystemLibrary.get_timer_remaining_time(p, 'FurinaP200Tick'); S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2:
            row('run %.2f' % (now - S['t0']))
            if now - S['t0'] > 1.0:
                S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P200_DBG2 armed')



