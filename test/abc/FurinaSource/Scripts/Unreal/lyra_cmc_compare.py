"""Lyra 에디터: 푸리나 폰(현재)과 Lyra 이전 백업의 CharacterMovement 속성 비교(앉기 속도 확인) -> Data/lyra_cmc_compare.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cmc_compare.json'
R = {}
PATHS = {'now': '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP', 'backup': '/Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero'}
def props(o):
    out = {'class': o.get_class().get_name()}
    for n in dir(o):
        if n.startswith('_') or not any(k in n for k in ('speed', 'crouch', 'braking', 'acceleration', 'ground_friction', 'jump', 'gravity', 'half_height', 'step', 'braking')): continue
        try:
            v = o.get_editor_property(n)
            if isinstance(v, (bool, int, float, str)): out[n] = v
        except Exception: pass
    return out
try:
    for k, p in PATHS.items():
        bp = unreal.load_asset(p)
        S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; comp = None
        for h in S.k2_gather_subobject_data_for_blueprint(bp):
            o = L.get_associated_object(L.get_data(h))
            if isinstance(o, unreal.CharacterMovementComponent): comp = o
        R[k] = props(comp) if comp else 'none'
        cdo = unreal.get_default_object(bp.generated_class()); R[k + '_cdo_cmc'] = props(cdo.get_editor_property('character_movement'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CMC', R.get('error', 'ok')[-200:])
