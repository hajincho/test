"""After pasting gen_fp_abp_t3d.py's nodes into ABP_Furina's AnimGraph: splice them between the locomotion
LayeredBoneBlend and the Control Rig, compile, save. Writes Data/fp_abp_connect.json.
All graph objects stay inside main(): py scripts share one global namespace, and node wrappers left in globals
crashed the editor on a later (re)compile when the reconstructed nodes were garbage collected."""
import unreal, os, json, traceback
def main():
    D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
    R = {}
    try:
        bp = unreal.load_asset('/Game/Furina/ABP_Furina')
        def nodes(cls): return list(unreal.AnimationLibrary.get_nodes_of_class(bp, cls, True))
        lbs = nodes(unreal.AnimGraphNode_LayeredBoneBlend)
        R['lbs'] = [n.get_name() for n in lbs]
        fp = [n for n in lbs if n.get_name().endswith('_FP')]
        base = [n for n in lbs if not n.get_name().endswith('_FP')]
        mc = [n for n in nodes(unreal.AnimGraphNode_ModifyCurve) if n.get_name().endswith('_Aim')]
        cr = nodes(unreal.AnimGraphNode_ControlRig)
        R['found'] = dict(fp=len(fp), base=len(base), mc=len(mc), cr=len(cr))
        if len(fp) == 1 and len(base) == 1 and len(mc) == 1 and len(cr) == 1:
            C = unreal.BlueprintGraphPinLibrary.try_create_connection
            R['base_to_fp'] = C(base[0].find_output_pin('Pose'), fp[0].find_input_pin('BasePose'))
            R['mc_to_cr'] = C(mc[0].find_output_pin('Pose'), cr[0].find_input_pin('Source'))
            R['cr_source_from'] = [p.get_owning_node().get_name() for p in cr[0].find_input_pin('Source').list_connected_pins()]
            pin = mc[0].find_input_pin('CurveValues_0')
            R['mc_pins'] = 'CurveValues_0 ok' if pin else 'no CurveValues_0 pin'
        del lbs, fp, base, mc, cr
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        R['status'] = str(bp.get_editor_property('status'))
        if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR:
            R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
        del bp
    except Exception:
        R['error'] = traceback.format_exc()
    json.dump(R, open(os.path.join(D, 'fp_abp_connect.json'), 'w'), indent=1, default=str)
    print('FP_ABP_CONNECT', R.get('status'), R.get('saved'))
main()
del main
