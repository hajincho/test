"""헤드리스: WBP_FurinaWeaponMenu 의 NationIndex 를 인스턴스 편집 가능으로(PIE 파이썬 확인용)."""
import unreal, json
R = {}
bp = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu'); BEL = unreal.BlueprintEditorLibrary
BEL.set_blueprint_variable_instance_editable(bp, 'NationIndex', True); BEL.compile_blueprint(bp)
R['status'] = str(bp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_wm_var_editable.json', 'w')); print('WM_VAR', R)
