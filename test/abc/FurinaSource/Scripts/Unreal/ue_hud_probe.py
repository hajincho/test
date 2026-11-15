"""Editor: member variables of ThirdPersonCharacter_BP (names containing 'Furina') and every node of BP_FurinaHUD's EventGraph with exec links -> Data/hud_probe.json"""
import unreal, json
def main():
    R = {}
    ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['vars'] = [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(ch) if 'Furina' in str(n) or 'Reload' in str(n) or 'Ammo' in str(n)]
    hb = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(hb, 'EventGraph')
    R['hud_vars'] = [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(hb)]
    nodes = {}
    for n in ed.list_all_nodes():
        pins = []
        for p in n.list_all_pins():
            conns = [(c.get_owning_node().get_name(), str(c.get_pin_name())) for c in p.list_connected_pins()]
            pins.append([str(p.get_pin_name()), p.get_pin_value(), conns])
        nodes[n.get_name()] = dict(title=str(n.get_node_title()), pins=pins)
    R['nodes'] = nodes
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\hud_probe.json', 'w'), indent=1, ensure_ascii=False); print('HUD_PROBE', len(nodes))
    del ed, hb, ch
main(); del main
