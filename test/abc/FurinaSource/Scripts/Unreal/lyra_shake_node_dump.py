"""Lyra 에디터(`py <파일>`): FPN_Shk* 노드의 핀 값과 연결, 경고/오류 노드 -> Data/lyra_shake_node_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shake_node_dump.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); names = {n.get_name(): n for n in ed.list_all_nodes()}
    for k in ('FPN_ShkNot', 'FPN_ShkBr', 'FPN_ShkStart', 'K2Node_FPF_CamMgr', 'K2Node_FPF_AdsOnF'):
        n = names.get(k); row = {}
        if n is None: R[k] = None; continue
        for pn in ('ShakeClass', 'Scale', 'PlaySpace', 'A', 'Condition', 'ReturnValue', 'self', 'then', 'else', 'execute'):
            try:
                p = n.find_input_pin(pn) or n.find_output_pin(pn)
                if p and p.is_valid(): row[pn] = {'val': str(p.get_pin_value()), 'conn': [c.get_owning_node().get_name() + '.' + c.get_name() for c in p.list_connected_pins()]}
            except Exception as e: row[pn + '_e'] = str(e)[:50]
        R[k] = row
    R['err_nodes'] = [n.get_name() for n in ed.list_nodes_with_errors()][:10]; R['warn_nodes'] = [n.get_name() for n in ed.list_nodes_with_warnings()][:10]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('SHAKE_NODE_DUMP')
