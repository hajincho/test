"""Lyra 에디터: 지금 에디터 프로세스에 걸려 있는 화질 관련 콘솔 변수 값 -> Data/lyra_cvar_now.json"""
import unreal, json
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cvar_now.json'
R = {}
for c in ('r.ScreenPercentage', 'sg.ShadowQuality', 'sg.GlobalIlluminationQuality', 'sg.ReflectionQuality', 'sg.PostProcessQuality', 'sg.EffectsQuality', 'sg.TextureQuality', 'sg.ResolutionQuality', 'sg.ViewDistanceQuality', 'sg.AntiAliasingQuality',
          'r.AntiAliasingMethod', 'r.TSR.History.ScreenPercentage', 'r.TemporalAA.Upsampling', 'r.Shadow.Virtual.Enable', 'r.Lumen.HardwareRayTracing', 'r.MipMapLODBias', 'r.MaxAnisotropy', 'r.Streaming.MipBias', 'r.DefaultFeature.MotionBlur', 'r.MotionBlurQuality', 'r.SecondaryScreenPercentage.GameViewport'):
    try: R[c] = unreal.SystemLibrary.get_console_variable_float_value(c)
    except Exception: R[c] = 'n/a'
json.dump(R, open(OUT, 'w'), indent=1); print('LYRA_CVAR_NOW', R)
