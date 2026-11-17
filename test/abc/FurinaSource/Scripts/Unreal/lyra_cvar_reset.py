"""Lyra 에디터: 성능 측정(lyra_perf_*.py) 때 런타임으로 바꿔 둔 화질 변수를 원래 값으로 되돌린다(화면 100%, sg.* 3).
콘솔 변수는 PIE 를 멈춰도 에디터 프로세스가 살아 있는 동안 유지되므로, 측정 후에는 반드시 호출해야 한다.  -> Data/lyra_cvar_reset.json"""
import unreal, json
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cvar_reset.json'
CMDS = ['r.ScreenPercentage 100', 'sg.ShadowQuality 3', 'sg.GlobalIlluminationQuality 3', 'sg.ReflectionQuality 3', 'sg.PostProcessQuality 3', 'sg.EffectsQuality 3']
R = {'cmds': CMDS}
for c in CMDS: unreal.SystemLibrary.execute_console_command(None, c)
for c in ('r.ScreenPercentage', 'sg.ShadowQuality', 'sg.GlobalIlluminationQuality', 'sg.ReflectionQuality', 'sg.PostProcessQuality', 'sg.EffectsQuality'):
    R[c] = unreal.SystemLibrary.get_console_variable_float_value(c)
json.dump(R, open(OUT, 'w'), indent=1); print('LYRA_CVAR_RESET', R)
