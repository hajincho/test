import unreal, os, json, traceback
D = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R = {}
try:
    for cn in ('BlueprintGraphLibrary', 'BlueprintGraphPin', 'EdGraph', 'K2Node', 'ControlRig', 'ControlRigBlueprint', 'AnimGraphNode_ControlRig', 'SkeletalMeshComponent', 'AnimationLibrary'):
        cls = getattr(unreal,cn,None)
        R['api_'+cn] = {k:getattr(cls,k).__doc__ for k in dir(cls or ()) if any(s in k for s in ('node','pin','link','default','rig','curve','execute','delta_time','evaluate','notify','pose')) and not k.startswith('_')}
    R['classes'] = [n for n in dir(unreal) if any(k in n for k in ('BlueprintGraph','GraphPin','GraphLibrary'))]
    for path in ('/Game/Furina/ABP_Furina','/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint'):
        bp = unreal.load_asset(path)
        R[path] = []
        for graph in unreal.BlueprintEditorLibrary.list_graphs(bp):
            gd = {'name':graph.get_name(),'methods':[n for n in dir(graph) if 'node' in n or 'pin' in n]}
            R[path].append(gd)
        R[path+'_animnodes'] = []
        for n in unreal.AnimationLibrary.get_nodes_of_class(bp, unreal.AnimGraphNode_Base, True):
            R[path+'_animnodes'].append({'name':n.get_name(),'class':n.get_class().get_name(),'node':n.get_editor_property('node').export_text() if hasattr(n,'node') else None})
except Exception: R['error'] = traceback.format_exc()
with open(os.path.join(D,'character_fix_api.json'),'w',encoding='utf-8') as f:json.dump(R,f,ensure_ascii=False,indent=1)
