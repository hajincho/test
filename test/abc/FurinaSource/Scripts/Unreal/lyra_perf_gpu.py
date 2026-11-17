"""Lyra PIE(Play 전에 무장): 설정을 누적 적용하며 단계마다 25초 워밍업(셰이더 컴파일 대기) 후 12초 CSV 프로파일(GPUTime 중앙값 비교용).
 단계: base(현재 ini) -> sg2(그림자/GI/반사/후처리/이펙트 품질 2) -> sp80(+ 화면 80%) -> sp70(+ 화면 70%)   -> Data/lyra_perf_gpu.json (각 단계의 CSV 시작 시각)"""
import unreal, json, time, traceback, os, glob
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_perf_gpu.json'
CSVDIR = r'C:\Users\fromj\Downloads\test\test\abc\Saved\Profiling\CSV'
R = {'phases': []}
PH = [('base', []), ('sg2', ['sg.ShadowQuality 2', 'sg.GlobalIlluminationQuality 2', 'sg.ReflectionQuality 2', 'sg.PostProcessQuality 2', 'sg.EffectsQuality 2']), ('sp80', ['r.ScreenPercentage 80']), ('sp70', ['r.ScreenPercentage 70'])]
S = {'i': -1, 'st': 'wait', 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def cmd(w, c): unreal.SystemLibrary.execute_console_command(w, c)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time()
        if S['st'] == 'wait':
            if unreal.GameplayStatics.get_player_pawn(w, 0) is None: return
            S['st'] = 'apply'; S['i'] = 0; S['t'] = now + 30
        if S['st'] == 'apply' and now >= S['t']:
            for c in PH[S['i']][1]: cmd(w, c)
            S['st'] = 'warm'; S['t'] = now + 25
        elif S['st'] == 'warm' and now >= S['t']:
            cmd(w, 'csvprofile start'); S['st'] = 'rec'; S['t'] = now + 12
        elif S['st'] == 'rec' and now >= S['t']:
            cmd(w, 'csvprofile stop'); R['phases'].append({'name': PH[S['i']][0], 'cmds': PH[S['i']][1], 'stopped_at': time.time()}); save()
            S['i'] += 1
            if S['i'] >= len(PH):
                for c in ('r.ScreenPercentage 100', 'sg.ShadowQuality 3', 'sg.GlobalIlluminationQuality 3', 'sg.ReflectionQuality 3', 'sg.PostProcessQuality 3', 'sg.EffectsQuality 3'): cmd(w, c)   # 측정 끝나면 화질 원복(안 하면 에디터 켜져 있는 동안 계속 남음)
                R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h']); return
            S['st'] = 'apply'; S['t'] = now + 2
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PERF_GPU armed')
