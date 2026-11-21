"""읽기 전용: HFX_ 노드 연결 덤프 -> Saved/HFXDump.json"""
import json
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph')
for n in ed.list_all_nodes():
    nm = n.get_name()
    if nm.startswith('HFX_') and any(k in nm for k in ('NS', 'Smoke', 'Flash', 'FxBranch')):
        pins = []
        for p in list(n.list_input_pins()) + list(n.list_output_pins()):
            pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:80], [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]])
        R[nm] = pins
R['done'] = True
(ROOT / 'Saved' / 'HFXDump.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
