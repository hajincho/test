"""읽기 전용: 권총 탄피 설치 상태 -> Saved/CaseInspect.json(소켓, 탄피 BP 그래프)"""
import json
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
for n in ('P38', 'P08', 'PP'):
    m = unreal.load_asset(f'/Game/Furina/FPVM/{n}/SK_FPVM_{n}'); R[n] = {'case_socket': bool(m.find_socket('VM_CaseFX')), 'muzzle_socket': bool(m.find_socket('VM_Muzzle')),
                                                                       'slots': [str(s.material_slot_name) for s in m.materials]}
for path in ('/Game/Furina/FX/Pistol/BP_FPVM_9mmCase', '/Game/Furina/M4/BP_223Case'):
    bp = unreal.load_asset(path); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); out = {}
    for nd in ed.list_all_nodes():
        pins = []
        for p in list(nd.list_input_pins()) + list(nd.list_output_pins()):
            pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:60], [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]])
        out[nd.get_name()] = [x for x in pins if x[2] or x[1] not in ('', 'None')]
    R[path] = out
pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph')
R['pawn_case_nodes'] = sorted(n.get_name() for n in ed.list_all_nodes() if n.get_name().startswith('PistolCase_'))
R['done'] = True; (ROOT / 'Saved' / 'CaseInspect.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
