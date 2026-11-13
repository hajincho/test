import unreal, os, json, traceback
D = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
try:
    for cn in ('BlueprintGraphEditor','BlueprintGraphPinLibrary','AnimGraphLibrary','ControlRigBlueprint','RigHierarchy'):
        cls=getattr(unreal,cn)
        R['api_'+cn]={k:getattr(cls,k).__doc__ for k in dir(cls) if not k.startswith('_') and not k in dir(unreal.Object)}
    for path in ('/Game/Furina/ABP_Furina','/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint'):
        bp=unreal.load_asset(path)
        R[path]=[]
        for n in unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_Base,True):
            try: nt=n.get_editor_property('node').export_text()
            except Exception as e:nt=str(e)
            R[path].append({'name':n.get_name(),'graph':n.get_outer().get_name(),'class':n.get_class().get_name(),'node':nt,'pins':[{ 'name':str(p.get_pin_name()),'value':p.get_pin_value(),'links':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]})
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'character_fix_graphs.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1)
