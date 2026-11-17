"""Lyra PIE(Play 전에 무장): PIE 시작 5초 뒤 CSV 프로파일러(FrameTime/GameThread/RenderThread/GPU)를 20초 기록 후 멈춘다.
tag 인자: py "<파일>" keep <tag>  -> Saved/Profiling/CSV 에 저장되고 경로는 Data/lyra_perf_csv_<tag>.json 에 기록. cvar 스냅샷도 같이 저장."""
import unreal, json, time, sys, traceback
TAG = sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1] != 'keep' else 'run'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_perf_csv_%s.json' % TAG
R = {'tag': TAG}; S = {'stage': 0, 't': 0}
CV = ('r.ScreenPercentage', 'r.Streaming.PoolSize', 'r.Shadow.Virtual.Enable', 'r.DynamicGlobalIlluminationMethod', 'r.ReflectionMethod', 'r.RayTracing', 'r.Lumen.HardwareRayTracing', 'r.AntiAliasingMethod',
      'r.Nanite', 'sg.ViewDistanceQuality', 'sg.ShadowQuality', 'sg.GlobalIlluminationQuality', 'sg.ReflectionQuality', 'sg.PostProcessQuality', 'sg.TextureQuality', 'sg.EffectsQuality', 't.MaxFPS', 'r.VSync')
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0 and pawn is not None: S['stage'] = 1; S['t'] = time.time()
        elif S['stage'] == 1 and time.time() - S['t'] > 5:
            R['cvars'] = {}
            for c in CV:
                try: R['cvars'][c] = unreal.SystemLibrary.get_console_variable_float_value(c) if hasattr(unreal.SystemLibrary, 'get_console_variable_float_value') else None
                except Exception: pass
            unreal.SystemLibrary.execute_console_command(w, 'csvprofile start'); S['stage'] = 2; S['t'] = time.time(); R['started'] = True; save()
        elif S['stage'] == 2 and time.time() - S['t'] > 20:
            unreal.SystemLibrary.execute_console_command(w, 'csvprofile stop'); S['stage'] = 3; R['stopped'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PERF armed', TAG)
