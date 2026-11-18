"""Lyra 에디터: 폰 EventGraph 의 P2_Lit*(권총<->소총 전환 때 소총을 오른손목에 다시 붙이는 상대 변환 리터럴) 노드 값과 연결 대상 -> Data/lyra_p2_lits.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_p2_lits.json'
R = {'lits': []}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if 'Lit' in nm and nm.startswith(('P2_', 'K2Node_P2')) or nm.startswith('P2_Lit'):
            row = {'node': nm}
            for p in n.list_all_pins():
                pn = str(p.get_pin_name())
                if pn == 'Value': row['value'] = str(p.get_pin_value())
                if pn == 'ReturnValue':
                    row['to'] = []
                    for c in p.list_connected_pins():
                        on = c.get_owning_node()
                        try: tt = str(on.get_node_title(unreal.NodeTitleType.FULL_TITLE)).replace('\n', ' ')[:50]
                        except Exception: tt = ''
                        row['to'].append([on.get_name(), str(c.get_pin_name()), tt])
            R['lits'].append(row)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_P2_LITS', len(R['lits']), R.get('error', '')[-200:])
