import unreal, os, json, traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
try:
    bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint')
    ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
    R['nodes']=[]
    for n in ed.list_all_nodes():
        R['nodes'].append({'name':n.get_name(),'title':n.get_node_title(),'class':n.get_class().get_name(),'pins':[{ 'name':str(p.get_pin_name()),'value':p.get_pin_value(),'links':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]})
    bs=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/WalkRun_BlendSpace')
    R['blendspace']={k:str(bs.get_editor_property(k)) for k in ('notify_trigger_mode','sample_data','axis_to_scale_animation')}
    bp=unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    rig=bp.create_control_rig()
    R['rig_methods']={n:getattr(rig,n).__doc__ for n in dir(rig) if any(k in n for k in ('hierarchy','init','reset','execute','time'))}
    R['rig_props']={n:str(rig.get_editor_property(n)) for n in ('hierarchy',)}
    R['anim_pose_api']={k:getattr(unreal.AnimationLibrary,k).__doc__ for k in dir(unreal.AnimationLibrary) if any(v in k for v in ('bone_pose','notify','meta_data_morph'))}
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'character_footsteps.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1)
