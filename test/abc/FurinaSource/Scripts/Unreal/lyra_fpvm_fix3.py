"""헤드리스: 캐릭터 BP 의 FurinaFPVM 컴포넌트 템플릿에 남은 재질 덮어쓰기(Kar98k 재질)를 비움 -> 메시를 G43 으로 바꿔도 Kar98k 재질이 쓰이던 문제 -> Data/lyra_fpvm_fix3.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'; R = {}
try:
    bp = unreal.load_asset(PAWN); sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    h = {str(lib.get_variable_name(lib.get_data(x))): x for x in sub.k2_gather_subobject_data_for_blueprint(bp)}['FurinaFPVM']
    c = lib.get_associated_object(lib.get_data(h)); ov = c.get_editor_property('override_materials'); R['before'] = [m.get_name() if m else None for m in ov]
    c.set_editor_property('override_materials', []); R['after'] = [m.get_name() if m else None for m in c.get_editor_property('override_materials')]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fpvm_fix3.json', 'w'), indent=1, default=str); print('FIX3', R)
