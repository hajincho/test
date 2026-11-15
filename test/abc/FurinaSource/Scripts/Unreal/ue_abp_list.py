"""Editor: every node of ABP_Furina's AnimGraph (name, class, pins with values and links) + the EventGraph node names -> Data/abp_nodes.json"""
import unreal, json
def main():
    ab = unreal.load_asset('/Game/Furina/ABP_Furina'); R = {}
    for gname in ('AnimGraph', 'EventGraph'):
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, gname); out = {}
        for n in ed.list_all_nodes():
            pins = []
            for p in n.list_all_pins():
                conns = [(c.get_owning_node().get_name(), str(c.get_pin_name())) for c in p.list_connected_pins()]
                if conns or (p.get_pin_value() not in ('', 'None')): pins.append([str(p.get_pin_name()), p.get_pin_value()[:60], conns])
            out[n.get_name()] = dict(cls=n.get_class().get_name(), title=str(n.get_node_title()), pins=pins)
        R[gname] = out; del ed
    R['vars'] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(ab)]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\abp_nodes.json', 'w'), indent=1, ensure_ascii=False); print('ABP_LIST', len(R['AnimGraph']), len(R['EventGraph']))
    del ab
main(); del main
