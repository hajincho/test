"""Lyra 에디터(`py <파일> 변수이름...`, 새로 시작한 에디터에서 한 번): ThirdPersonCharacter_BP 의 멤버 변수를 '인스턴스 편집 가능'으로 바꿔 PIE 파이썬에서 set_editor_property 로 조절할 수 있게 한다.  -> Data/lyra_bp_vars_editable.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bp_vars_editable.json'
NAMES = [a for a in sys.argv[1:] if not a.endswith('.py')] or ['FurinaPFLocX', 'FurinaPFLocY', 'FurinaPFLocZ', 'FurinaPFRotP', 'FurinaPFRotY', 'FurinaPFRotR']
R = {'names': NAMES, 'log': []}
try:
    bp = unreal.load_asset(PAWN); BEL = unreal.BlueprintEditorLibrary
    for n in NAMES:
        try: BEL.set_blueprint_variable_instance_editable(bp, n, True); R['log'].append([n, 'ok'])
        except Exception as e: R['log'].append([n, str(e)[:120]])
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str); print('LYRA_BP_VARS_EDITABLE', R.get('status'), R.get('error', ''))
import gc; gc.collect()
