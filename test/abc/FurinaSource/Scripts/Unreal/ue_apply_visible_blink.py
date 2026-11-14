"""Apply morph-capable face shaders and explicitly forward evaluated blink weight."""
import unreal,os,json,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={'saved':[],'stage_only':os.path.exists(os.path.join(D,'walk_blink_stage_only'))}
def wire(a,b):
    assert a.is_valid() and b.is_valid()
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
try:
    bp=unreal.load_asset('/Game/Furina/ABP_Furina')
    ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
    marker='Furina: apply the evaluated blink to the rendered mesh'
    event=ed.find_event_node('BlueprintPostEvaluateAnimation')
    linked=[p.get_owning_node() for p in event.find_then_pin().list_connected_pins()] if event else []
    has_bridge=any(n.find_input_pin('MorphTargetName').is_valid() and n.find_input_pin('MorphTargetName').get_pin_value()=='IdleBlink' for n in linked)
    if not has_bridge:
        if not event:event=unreal.BlueprintEditorLibrary.add_event_override(bp,'BlueprintPostEvaluateAnimation',unreal.IntPoint(0,0))
        assert event
        targets=list(event.find_then_pin().list_connected_pins())
        get_mesh=ed.add_call_function_node('/Script/Engine.AnimInstance:GetOwningComponent')
        get_mesh.set_node_pos(unreal.IntPoint(0,180))
        get_curve=ed.add_call_function_node('/Script/Engine.AnimInstance:GetCurveValue')
        get_curve.set_node_pos(unreal.IntPoint(0,350))
        assert get_curve.find_input_pin('CurveName').set_pin_value('IdleBlink')
        apply=ed.add_call_function_node('/Script/Engine.SkeletalMeshComponent:SetMorphTarget')
        apply.set_node_pos(unreal.IntPoint(400,0))
        assert apply.find_input_pin('MorphTargetName').set_pin_value('IdleBlink')
        assert apply.find_input_pin('bRemoveZeroWeight').set_pin_value('true')
        wire(get_mesh.find_result_pin(),apply.find_self_pin())
        wire(get_curve.find_result_pin(),apply.find_input_pin('Value'))
        event.find_then_pin().break_pin_links()
        wire(event.find_then_pin(),apply.find_execute_pin())
        for target in targets:wire(apply.find_then_pin(),target)
    # The UE 5.8 API creates comment nodes without a usable GUID. The connected
    # SetMorphTarget node is the idempotency marker; remove the old staging label.
    for comment in ed.list_comment_nodes():
        if str(unreal.BlueprintEditorLibrary.get_comment_text(comment))==marker:
            ed.remove_comment_node(comment)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
    material=unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque')
    R['material_before']={n:bool(material.get_editor_property(n)) for n in ('used_with_skeletal_mesh','used_with_morph_targets')}
    material.set_editor_property('used_with_skeletal_mesh',True)
    material.set_editor_property('used_with_morph_targets',True)
    unreal.MaterialEditingLibrary.recompile_material(material)
    R['material_after']={n:bool(material.get_editor_property(n)) for n in ('used_with_skeletal_mesh','used_with_morph_targets')}
    if not R['stage_only']:
        for a in (bp,material):
            assert unreal.EditorAssetLibrary.save_loaded_asset(a,False)
            R['saved'].append(a.get_path_name())
    R['ok']=True
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'visible_blink_applied.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1,default=str)
