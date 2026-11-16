"""Lyra 에디터(`py <파일> keep`): 푸리나 폰 `Get Look Rate` 가 이전 프로젝트의 레거시 입력 배율(InputYawScale 2.5 / InputPitchScale -2.5)을 전제로 만들어져 있어
Lyra(DefaultGame.ini 에서 둘 다 1.0)에서는 마우스 상하가 반전되고 감도가 2.5분의 1이 된다. 함수가 배율을 직접 곱하도록 상수를 바꾼다:
  K2Node_CallFunction_10 (InvertLookUp? 선택): A(반전 켬) -1 -> +2.5, B(반전 끔) +1 -> -2.5   (상하: 반전 끔 = 마우스 위로 올리면 위를 봄)
  K2Node_CallFunction_0  (Up/Down? 선택): B(좌우) 1.0 -> 2.5
-> Data/lyra_fix_look.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_look.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'Get Look Rate'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    sel10, sel0 = nodes['K2Node_CallFunction_10'], nodes['K2Node_CallFunction_0']
    R['before'] = {'sel10': [sel10.find_input_pin('A').get_pin_value(), sel10.find_input_pin('B').get_pin_value()], 'sel0_B': sel0.find_input_pin('B').get_pin_value()}
    if R['before']['sel10'] == ['-1.000000', '1.000000'] and R['before']['sel0_B'] == '1.000000':
        sel10.find_input_pin('A').set_pin_value('2.5'); sel10.find_input_pin('B').set_pin_value('-2.5'); sel0.find_input_pin('B').set_pin_value('2.5'); R['changed'] = True
    else: R['changed'] = False
    R['after'] = {'sel10': [sel10.find_input_pin('A').get_pin_value(), sel10.find_input_pin('B').get_pin_value()], 'sel0_B': sel0.find_input_pin('B').get_pin_value()}
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_LOOK', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
