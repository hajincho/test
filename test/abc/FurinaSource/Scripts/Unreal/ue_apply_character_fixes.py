"""Apply the blink, knee-pole, and walk-footstep fixes in place. Idempotent."""
import unreal, os, json, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={'saved':[]}
E=unreal.EditorAssetLibrary
STAGE_ONLY=os.path.exists(os.path.join(D,'character_fix_stage_only'))

def save(asset):
    if STAGE_ONLY:
        R.setdefault('staged',[]).append(asset.get_path_name())
        return
    assert E.save_loaded_asset(asset,False), 'Could not save '+asset.get_path_name()
    R['saved'].append(asset.get_path_name())

def wire(out_pin,in_pin):
    assert out_pin.is_valid() and in_pin.is_valid(), 'Invalid Blueprint pin'
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(out_pin,in_pin), 'Blueprint connection failed'

try:
    bp=unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    c=bp.get_controller()
    bp.set_auto_vm_recompile(False)
    def default(pin,value):assert c.set_pin_default_value(pin,value,True,False),pin
    for side,sign,y in (('L',1,-2600),('R',-1,-1900)):
        name=side+'PolePos'
        if not c.get_graph().find_node_by_name(name):
            assert c.add_unit_node_from_struct_path(unreal.RigUnit_MathVectorAdd.static_struct().get_path_name(),'Execute',unreal.Vector2D(700,y+700),name)
        default(name+'.B','(X=%f,Y=50,Z=0)'%(sign*6.0))
        # Source disconnects are explicit; an existing connection can be preserved on reruns.
        target=c.get_graph().find_pin(side+'IK.PoleVector')
        for source in target.get_linked_source_pins():c.break_link(source.get_pin_path(),target.get_pin_path(),False)
        if not c.get_graph().find_pin(name+'.A').get_linked_source_pins():assert c.add_link(side+'Thigh.Transform.Translation',name+'.A',False)
        assert c.add_link(name+'.Result',side+'IK.PoleVector',False)
        default(side+'IK.PoleVectorKind','Location')
    default('IKWs.B','1')
    pin=c.get_graph().find_pin('BlinkOut.B')
    for source in pin.get_linked_source_pins():c.break_link(source.get_pin_path(),pin.get_pin_path(),False)
    default('BlinkOut.B','1')
    bp.set_auto_vm_recompile(True);bp.recompile_vm()
    assert bp.get_editor_property('status')==unreal.BlueprintStatus.BS_UP_TO_DATE
    save(bp)

    sk=unreal.load_asset('/Game/Furina/SK_Furina_Skeleton')
    unreal.AnimationLibrary.set_curve_meta_data_morph_target(sk,'IdleBlink',True)
    assert unreal.AnimationLibrary.get_curve_meta_data_morph_target(sk,'IdleBlink')
    save(sk)

    # Source mannequin notifies have a different cadence to the visible walk clip.
    # Keep the original sprint path, and let the visible walk clip own walking audio.
    manny=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint')
    ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(manny,'EventGraph')
    nodes=ed.list_all_nodes()
    marker='Furina walk audio: visible walk clip owns footsteps'
    found=[n for n in ed.list_comment_nodes() if str(unreal.BlueprintEditorLibrary.get_comment_text(n))==marker]
    if not found:
        event=ed.find_event_node('AnimNotify_Footstep')
        assert event
        after_ground=next(p.get_owning_node() for p in event.find_then_pin().list_connected_pins())
        ground_pin=after_ground.find_output_pin('else')
        targets=list(ground_pin.list_connected_pins())
        assert targets
        # Reuse an unconnected branch from an interrupted staging attempt.
        empty=[n for n in ed.list_nodes_of_class(unreal.K2Node_IfThenElse) if not any(p.list_connected_pins() for p in n.list_all_pins())]
        gate=empty[0] if empty else ed.add_branch_node()
        gate.set_node_pos(unreal.IntPoint(-500,420))
        cv=ed.add_call_function_node('/Script/Engine.AnimInstance:GetCurveValue')
        cv.set_node_pos(unreal.IntPoint(-1050,700))
        assert cv.find_input_pin('CurveName').set_pin_value('FurinaWalk')
        cmp=ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Greater_DoubleDouble')
        cmp.set_node_pos(unreal.IntPoint(-750,700))
        wire(cv.find_result_pin(),cmp.find_input_pin('A'))
        assert cmp.find_input_pin('B').set_pin_value('0.5')
        wire(cmp.find_result_pin(),gate.find_input_pin('Condition'))
        ground_pin.break_pin_links();wire(ground_pin,gate.find_execute_pin())
        for target in targets:wire(gate.find_output_pin('else'),target)
        ed.add_comment_to_nodes(marker,[gate,cv,cmp],45)
    # Discard only isolated helper nodes left by an interrupted pre-save attempt.
    orphan_helpers=[]
    for n in ed.list_all_nodes():
        if any(p.list_connected_pins() for p in n.list_all_pins()):continue
        curve_pin=n.find_input_pin('CurveName')
        if (curve_pin.is_valid() and curve_pin.get_pin_value()=='FurinaWalk') or (n.get_class().get_name()=='K2Node_PromotableOperator' and n.get_node_title()=='float > float'):
            orphan_helpers.append(n)
    if orphan_helpers:ed.remove_nodes(orphan_helpers)
    unreal.BlueprintEditorLibrary.compile_blueprint(manny)
    R['manny_status']=str(manny.get_editor_property('status'))
    assert manny.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
    save(manny)

    seq=unreal.load_asset('/Game/Furina/Anim/AS_Furina_Walk')
    track='FurinaWalkSteps'
    if track in [str(n) for n in unreal.AnimationLibrary.get_animation_notify_track_names(seq)]:
        unreal.AnimationLibrary.remove_animation_notify_events_by_track(seq,track)
    else:unreal.AnimationLibrary.add_animation_notify_track(seq,track,unreal.LinearColor(.25,.6,1,1))
    cue=unreal.load_asset('/Game/3DPlatformerGameBundle/Audio/Cues/Footsteps2_Cue')
    R['walk_notifies']=[]
    # Forward-most ankle positions in the 40-frame / 30 fps recorded walk cycle.
    for time,bone in ((2/30,'Right-ankle'),(22/30,'Left-ankle')):
        notify=unreal.AnimNotify_PlaySound(outer=seq)
        notify.set_editor_property('sound',cue)
        notify.set_editor_property('volume_multiplier',.28)
        notify.set_editor_property('pitch_multiplier',1.05)
        notify.set_editor_property('follow',True)
        notify.set_editor_property('attach_name',bone)
        ev=unreal.AnimNotifyEvent()
        ev.set_editor_property('notify',notify)
        ev.set_editor_property('trigger_weight_threshold',.5)
        ev.set_editor_property('notify_name','FurinaWalkStep')
        unreal.AnimationLibrary.add_animation_notify_event_from_source(seq,time,ev,track)
        R['walk_notifies'].append({'time':time,'bone':bone,'volume':.28,'pitch':1.05,'weight_threshold':.5})
    save(seq)
    furina=unreal.load_asset('/Game/Furina/ABP_Furina')
    unreal.BlueprintEditorLibrary.compile_blueprint(furina)
    assert furina.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
    save(furina)
    R['ok']=True
    R['stage_only']=STAGE_ONLY
except Exception:R['error']=traceback.format_exc()
finally:
    if 'bp' in globals():bp.set_auto_vm_recompile(True)
with open(os.path.join(D,'character_fixes_applied.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1,default=str)
print('CHARACTER_FIXES_APPLIED',R.get('ok',False))
