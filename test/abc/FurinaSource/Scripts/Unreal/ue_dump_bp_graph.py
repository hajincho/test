"""Dumps nodes of any blueprint graph. usage: py ue_dump_bp_graph.py <asset path> <graph name> [name substring ...] -> Data/dump_bp_graph.json"""
import unreal, json, sys
def main():
    asset, graph = sys.argv[1], sys.argv[2]; keys = sys.argv[3:]
    bp = unreal.load_asset(asset)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, graph)
    R = {}
    for n in ed.list_all_nodes():
        name = n.get_name()
        if keys and not any(k in name for k in keys): continue
        pins = []
        for p in n.list_all_pins():
            conns = [(p2.get_owning_node().get_name(), str(p2.get_pin_name())) for p2 in p.list_connected_pins()]
            pins.append([str(p.get_pin_name()), p.get_pin_value(), conns])
        R[name] = dict(title=str(n.get_node_title()), pins=pins)
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\dump_bp_graph.json', 'w'), indent=1, ensure_ascii=False)
    print('DUMP_BP_GRAPH', len(R)); del ed, bp
main(); del main
