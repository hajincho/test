"""Lyra 에디터: 푸리나 폰/ABP EventGraph 에서 InterpSpeed 핀을 가진 노드와 값/연결(견착 카메라 보간 후보 찾기) -> Data/lyra_speed_scan.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_speed_scan.json'
R = {}
try:
    for k, p in (('pawn', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'), ('abp', '/Game/Furina/ABP_Furina')):
        bp = unreal.load_asset(p); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); rows = []
        for n in ed.list_all_nodes():
            try:
                pin = n.find_input_pin('InterpSpeed')
                if pin and pin.is_valid():
                    rows.append({'node': n.get_name(), 'speed': str(pin.get_pin_value()), 'speed_from': [c.get_owning_node().get_name() for c in pin.list_connected_pins()],
                                 'target_from': [c.get_owning_node().get_name() for c in n.find_input_pin('Target').list_connected_pins()] if n.find_input_pin('Target').is_valid() else None,
                                 'ret_to': [c.get_owning_node().get_name() for c in n.find_output_pin('ReturnValue').list_connected_pins()][:3]})
            except Exception: pass
        R[k] = rows
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SPEED_SCAN', R.get('error', 'ok')[-200:])
