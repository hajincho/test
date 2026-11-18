"""Lyra 에디터(`py <파일> <경험이름|none>`): PIE 에서 쓸 경험 오버라이드(LyraDeveloperSettings.ExperienceOverride)를 바꾼다. 예) py <파일> B_ShooterGame_Elimination ,  none 이면 오버라이드 해제(맵의 기본 경험).
(Config/DefaultEditorPerProjectUserSettings.ini 의 ExperienceOverride 는 건드리지 않는다. 에디터 실행 중의 설정 객체만 바꾼다. 기본값 B_Furina_Experience 로 되돌리려면 `py <파일> B_Furina_Experience`.)  -> Data/lyra_set_experience_override.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_set_experience_override.json'
R = {}
try:
    name = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'B_Furina_Experience'
    cdo = unreal.get_default_object(unreal.LyraDeveloperSettings); R['before'] = str(cdo.get_editor_property('experience_override'))
    cdo.set_editor_property('experience_override', unreal.PrimaryAssetId() if name == 'none' else unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), name))
    R['after'] = str(cdo.get_editor_property('experience_override')); R['name'] = name
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_EXP_OVERRIDE', R.get('after'), R.get('error', '')[-200:])
