"""Lyra 에디터(`py <파일> [강도]`): /Game/Furina/CameraShakes/CS_FurinaShot 카메라 셰이크 에셋의 패턴을 (다시) 설정한다. 설정 → 컴파일 → 저장 → CDO 재조회로 패턴이 남았는지 확인.  -> Data/lyra_shake_asset.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shake_asset.json'
SHAKE = '/Game/Furina/CameraShakes/CS_FurinaShot'
nums = [a for a in sys.argv[1:] if a.replace('.', '', 1).isdigit()]
GAIN = float(nums[0]) if nums else 1.0
R = {'gain': GAIN}
try:
    bp = unreal.load_asset(SHAKE); cdo = unreal.get_default_object(bp.generated_class())
    R['before'] = str(cdo.get_root_shake_pattern())
    pat = unreal.new_object(unreal.WaveOscillatorCameraShakePattern, outer=cdo)
    pat.set_editor_property('duration', 0.18); pat.set_editor_property('blend_in_time', 0.015); pat.set_editor_property('blend_out_time', 0.12)
    for axis, amp, freq in (('pitch', 0.55, 34.0), ('yaw', 0.40, 27.0), ('roll', 0.50, 31.0)):
        o = pat.get_editor_property(axis); o.set_editor_property('amplitude', amp * GAIN); o.set_editor_property('frequency', freq); pat.set_editor_property(axis, o)
    R['pat_vals'] = [str(pat.get_editor_property(a)) for a in ('pitch', 'yaw', 'roll')]
    pat.set_editor_property('rotation_amplitude_multiplier', 1.0); pat.set_editor_property('rotation_frequency_multiplier', 1.0); pat.set_editor_property('location_amplitude_multiplier', 0.0); pat.set_editor_property('location_frequency_multiplier', 1.0)
    cdo.set_root_shake_pattern(pat); bp.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo2 = unreal.get_default_object(bp.generated_class()); R['after_compile'] = str(cdo2.get_root_shake_pattern())
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SHAKE_ASSET', R.get('error', '')[-300:])
