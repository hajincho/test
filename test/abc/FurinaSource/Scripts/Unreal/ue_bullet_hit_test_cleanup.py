"""Editor(PIE 중지 후): 히트판정 테스트 잔재 제거 -> 총알 BP의 FurinaDamageEffect 기본값 비움, 레벨의 FurinaTestDummy 삭제, 스텁 GE와 BP_FurinaTestDummy 에셋 삭제, 레벨 저장.
-> Data/bullet_hit_test_cleanup.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_hit_test_cleanup.json'
R = {}
try:
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('FurinaDamageEffect', None)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['bullet_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    R['effect_default'] = str(unreal.get_default_object(bp.generated_class()).get_editor_property('FurinaDamageEffect'))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == 'FurinaTestDummy': eas.destroy_actor(a); n += 1
    R['dummies_removed'] = n
    R['level_saved'] = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    for p in ('/Game/Furina/QA/BP_FurinaTestDummy', '/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller'):
        R['deleted ' + p] = unreal.EditorAssetLibrary.delete_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else 'absent'
    R['left_in_gameplayeffects'] = unreal.EditorAssetLibrary.list_assets('/Game/GameplayEffects', recursive=True)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w'), indent=1, default=str); print('HIT_TEST_CLEANUP', R)
