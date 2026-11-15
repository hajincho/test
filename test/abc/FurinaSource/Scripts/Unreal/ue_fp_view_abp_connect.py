"""Inserts the pasted ModifyCurve_ViewState (ViewTP) between ModifyCurve_AimState and the Control Rig node, compiles, saves."""
import unreal, json
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/ABP_Furina')
    mcs = unreal.AnimationLibrary.get_nodes_of_class(bp, unreal.AnimGraphNode_ModifyCurve, True)
    R['mcs'] = [n.get_name() for n in mcs]
    aim = [n for n in mcs if n.get_name().endswith('_AimState')][0]
    st = [n for n in mcs if 'ViewState' in n.get_name()][0]
    out = aim.find_output_pin('Pose')
    targets = [p for p in out.list_connected_pins() if p.get_owning_node() != st]
    R['old_targets'] = [p.get_owning_node().get_name() for p in targets]
    R['in'] = unreal.BlueprintGraphPinLibrary.try_create_connection(out, st.find_input_pin('SourcePose'))
    for t in targets:
        R.setdefault('out', []).append(unreal.BlueprintGraphPinLibrary.try_create_connection(st.find_output_pin('Pose'), t))
    R['st_out_to'] = [p.get_owning_node().get_name() for p in st.find_output_pin('Pose').list_connected_pins()]
    R['aim_out_to'] = [p.get_owning_node().get_name() for p in out.list_connected_pins()]
    del mcs, aim, st, out, targets
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR:
        R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_view_abp_connect.json', 'w'), indent=1, default=str)
    print('VIEW_ABP', R)
main()
del main
