"""Lyra 에디터(`py <파일>`): 카메라 셰이크 관련 파이썬 노출 확인 -> Data/lyra_shake_probe.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shake_probe.json'
R = {'unreal_names': [n for n in dir(unreal) if 'Shake' in n]}
try:
    for cn in ('PerlinNoiseCameraShakePattern', 'WaveOscillatorCameraShakePattern', 'CameraShakeBase', 'LegacyCameraShake', 'SimpleCameraShakePattern'):
        c = getattr(unreal, cn, None)
        if c:
            R[cn] = [n for n in dir(c) if not n.startswith('_') and not callable(getattr(c, n, None))][:60]
    cb = unreal.CameraShakeBase.static_class(); R['base_props'] = [n for n in dir(unreal.get_default_object(unreal.CameraShakeBase)) if not n.startswith('_') and 'pattern' in n.lower()]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SHAKE_PROBE')
