"""Connects LayeredBoneBlend_FP.Pose -> ModifyCurve_Aim.SourcePose (the pasted link went to a misnamed orphan pin), compiles, saves."""
import unreal, json
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/ABP_Furina')
    lb = [n for n in unreal.AnimationLibrary.get_nodes_of_class(bp, unreal.AnimGraphNode_LayeredBoneBlend, True) if n.get_name().endswith('_FP')][0]
    mc = [n for n in unreal.AnimationLibrary.get_nodes_of_class(bp, unreal.AnimGraphNode_ModifyCurve, True) if n.get_name().endswith('_Aim')][0]
    src = mc.find_input_pin('SourcePose')
    out = lb.find_output_pin('Pose')
    R['pins_found'] = [bool(src), bool(out)]
    R['linked'] = unreal.BlueprintGraphPinLibrary.try_create_connection(out, src)
    R['mc_source_from'] = [p.get_owning_node().get_name() for p in src.list_connected_pins()]
    del lb, mc, src, out
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR:
        R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_abp_fixlink.json', 'w'), indent=1)
    print('FIXLINK', R)
main()
del main
