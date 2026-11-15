"""Dumps the EventGraph nodes of ThirdPersonCharacter_BP whose name matches the argument (substring, default FPF_) with input pins
(default values + connections) -> Data/dump_char_graph.json. usage: py ue_dump_char_graph.py [substring ...]"""
import unreal, json, sys
def main():
    keys = sys.argv[1:] or ['FPF_']
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    R = {}
    for n in ed.list_all_nodes():
        name = n.get_name()
        if not any(k in name for k in keys): continue
        pins = []
        for p in n.list_all_pins():
            conns = [(p2.get_owning_node().get_name(), str(p2.get_pin_name())) for p2 in p.list_connected_pins()]
            pins.append([str(p.get_pin_name()), p.get_pin_value(), conns])
        R[name] = dict(title=str(n.get_node_title()), pins=pins)
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\dump_char_graph.json', 'w'), indent=1, ensure_ascii=False)
    print('DUMP_CHAR_GRAPH', len(R))
    del ed, bp
main(); del main
