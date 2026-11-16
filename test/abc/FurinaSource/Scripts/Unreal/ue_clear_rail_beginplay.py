"""Furina in levels without rails (2026-11-16, Underground Tunnel): the bundle's Grind_Rail_Component_BP reports UsingRail? = True from the first frame (its tick stays disabled where there is no rail, so nothing resets it),
which turns the FurinaSpecial flag on: first person is not possible and the rifle does not fire. Fix: ThirdPersonCharacter_BP BeginPlay (after the near-clip console command) -> Set Grind_Rail_Component_BP.UsingRail? = false.
Components begin play before the actor's BeginPlay, so this runs after the component has set its value. Real rail riding sets it true later, as before."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    names = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FPN_ClearRailSet' not in names:
        anchor = names.get('FPN_NearClip') or ed.find_event_node('ReceiveBeginPlay'); assert anchor, 'no BeginPlay anchor'
        cls = unreal.load_asset('/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP').generated_class()
        get = ed.add_get_member_variable_node('Grind_Rail_Component_BP'); get.rename('FPN_ClearRailGet')
        st = ed.add_set_member_variable_node('UsingRail?', cls.get_path_name()); st.rename('FPN_ClearRailSet'); st.find_input_pin('UsingRail?').set_pin_value('false')
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(get.find_output_pin('Grind_Rail_Component_BP'), st.find_self_pin())
        old = list(anchor.find_then_pin().list_connected_pins()); anchor.find_then_pin().break_pin_links()
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(anchor.find_then_pin(), st.find_execute_pin())
        for p in old: assert unreal.BlueprintGraphPinLibrary.try_create_connection(st.find_then_pin(), p)
        R['added'] = True; R['anchor'] = anchor.get_name()
    del ed, names
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\clear_rail_beginplay.json', 'w'), indent=1)
print('CLEAR_RAIL', R.get('status'), R.get('error', '')[:300])
