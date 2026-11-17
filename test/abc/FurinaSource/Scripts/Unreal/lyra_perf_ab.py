"""Lyra PIE(Play 전에 무장): 렌더 설정을 하나씩 바꿔가며 평균 프레임 시간을 잰다(실시간 dt). 각 단계 3초 안정화 + 8초 측정.
 단계: 워밍업, base 를 사이사이 반복하며 HWRT off / VSM off / 화면 75% / sg.* 품질 2 / 합친 것 비교.  -> Data/lyra_perf_ab.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_perf_ab.json'
R = {'phases': []}
RESET = ['r.Lumen.HardwareRayTracing 1', 'r.Shadow.Virtual.Enable 1', 'r.ScreenPercentage 100', 'sg.ShadowQuality 3', 'sg.GlobalIlluminationQuality 3', 'sg.ReflectionQuality 3', 'sg.PostProcessQuality 3', 'sg.EffectsQuality 3']
PH = [('warmup', []), ('base1', []), ('hwrt_off', ['r.Lumen.HardwareRayTracing 0']), ('base2', []), ('vsm_off', ['r.Shadow.Virtual.Enable 0']), ('base3', []),
      ('screen75', ['r.ScreenPercentage 75']), ('base4', []), ('sg2', ['sg.ShadowQuality 2', 'sg.GlobalIlluminationQuality 2', 'sg.ReflectionQuality 2', 'sg.PostProcessQuality 2', 'sg.EffectsQuality 2']), ('base5', []),
      ('combo', ['r.Lumen.HardwareRayTracing 0', 'r.Shadow.Virtual.Enable 0', 'r.ScreenPercentage 75'])]
S = {'i': -1, 'state': 'wait_pawn', 't': 0, 'dts': []}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def cmd(w, c): unreal.SystemLibrary.execute_console_command(w, c)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time()
        if S['state'] == 'wait_pawn':
            if unreal.GameplayStatics.get_player_pawn(w, 0) is None: return
            S['state'] = 'start_phase'; S['t'] = now; S['i'] = 0; S['pending'] = True; S['t'] = now + 20   # 시작 히치/셰이더 컴파일 대기
        if S['state'] == 'start_phase' and now >= S['t']:
            for c in RESET: cmd(w, c)
            for c in PH[S['i']][1]: cmd(w, c)
            S['state'] = 'settle'; S['t'] = now + 3
        elif S['state'] == 'settle' and now >= S['t']:
            S['state'] = 'measure'; S['t'] = now + 8; S['dts'] = []
        elif S['state'] == 'measure':
            S['dts'].append(dt)
            if now >= S['t']:
                v = sorted(S['dts']); n = len(v)
                R['phases'].append({'name': PH[S['i']][0], 'frames': n, 'avg_ms': round(1000 * sum(v) / n, 1), 'avg_fps': round(n / sum(v), 1), 'p95_ms': round(1000 * v[int(n * .95)], 1)}); save()
                S['i'] += 1
                if S['i'] >= len(PH):
                    for c in RESET: cmd(w, c)
                    R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h']); return
                S['state'] = 'start_phase'; S['t'] = now
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PERF_AB armed')
