"""Route the bounded Control Rig hair directly to the final local pose."""
import unreal, os, json, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={'saved':[],'stage_only':os.path.exists(os.path.join(D,'hair_stage_only'))}
try:
    bp=unreal.load_asset('/Game/Furina/ABP_Furina')
    crs=unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_ControlRig,True)
    roots=unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_Root,True)
    assert len(crs)==len(roots)==1
    pin=roots[0].find_input_pin('Result')
    R['previous_output']=[p.get_owning_node().get_name() for p in pin.list_connected_pins()]
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(crs[0].find_output_pin('Pose'),pin)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
    R['output']=[p.get_owning_node().get_name() for p in pin.list_connected_pins()]
    R['dynamics_connected_to_output']=any('AnimDynamics' in p for p in R['output'])
    if not R['stage_only']:
        assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
        R['saved'].append(bp.get_path_name())
        rig=unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
        assert unreal.EditorAssetLibrary.save_loaded_asset(rig,False)
        R['saved'].append(rig.get_path_name())
    R['ok']=True
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'soft_hair_applied.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1)
