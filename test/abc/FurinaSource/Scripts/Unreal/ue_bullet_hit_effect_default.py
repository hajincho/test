"""BP_FurinaBullet 의 FurinaDamageEffect / FurinaDamage 기본값 읽기/설정. usage: py ue_bullet_hit_effect_default.py [set|clear|show]  -> Data/bullet_hit_effect_default.json
set: 테스트용 스텁 GE(/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller)로 지정, clear: 비움(Lyra에서 지정)"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_hit_effect_default.json'
R = {}
try:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'show'
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); cdo = unreal.get_default_object(bp.generated_class())
    R['before'] = str(cdo.get_editor_property('FurinaDamageEffect')); R['damage'] = cdo.get_editor_property('FurinaDamage')
    if mode == 'set':
        cdo.set_editor_property('FurinaDamageEffect', unreal.load_class(None, '/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller.GE_Damage_Basic_SetByCaller_C'))
    elif mode == 'clear':
        cdo.set_editor_property('FurinaDamageEffect', None)
    if mode != 'show':
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
        R['after'] = str(unreal.get_default_object(bp.generated_class()).get_editor_property('FurinaDamageEffect'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w'), indent=1, default=str); print('BULLET_EFFECT_DEFAULT', R)
