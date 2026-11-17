"""Lyra 에디터: 앉기 전환 속도에 관여하는 값 조사 -> Data/lyra_crouch_rate_probe.json
 1) ABP_Furina EventGraph/AnimGraph 에서 이름에 Crouch 가 든 노드(+Interp 계열)와 핀 값
 2) CR_FurinaSecondary 의 CrouchW / ShW / AdsW 블렌드 값
 3) 푸리나 폰 EventGraph 중 Crouch/Interp 노드"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_crouch_rate_probe.json'
R = {}
def dump_graph(bp, gname, keys):
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, gname); rows = []
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if any(k.lower() in nm.lower() for k in keys):
            row = {'node': nm}
            try: row['pins'] = [[str(p.get_pin_name()), str(p.get_pin_value())[:50], [c.get_owning_node().get_name() for c in p.list_connected_pins()][:3]] for p in n.list_all_pins() if str(p.get_pin_value()) or p.list_connected_pins()][:10]
            except Exception as e: row['err'] = str(e)[:60]
            rows.append(row)
    return rows
try:
    abp = unreal.load_asset('/Game/Furina/ABP_Furina')
    for g in ('EventGraph', 'AnimGraph'):
        try: R['abp_' + g] = dump_graph(abp, g, ('Crouch', 'Interp', 'FInterp'))
        except Exception as e: R['abp_' + g + '_err'] = str(e)[:100]
    pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['pawn'] = dump_graph(pawn, 'EventGraph', ('Interp', 'CrouchTime', 'CrB', 'DoCrouch', 'DoStand'))
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph(); R['cr'] = {}
    for n in g.get_nodes():
        if str(n.get_node_path()) in ('CrouchW', 'ShW', 'AdsW'):
            R['cr'][str(n.get_node_path())] = [[str(p.get_name()), str(p.get_default_value())] for p in n.get_pins()]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CROUCH_RATE', R.get('error', 'ok')[-200:])
