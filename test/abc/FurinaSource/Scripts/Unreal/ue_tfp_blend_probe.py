import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph');R['actions']=[x for x in e.list_available_nodes([]) if any(y in x for y in ('BS_Unarmed','CrouchMovement','시퀀스','애니메이션|블렌드'))]
for p in ['/Game/Furina/TFP/Anim/BS_Unarmed_F','/Game/Furina/TFP/Anim/BS_CrouchMovement_F']:
 a=unreal.load_asset(p)
 if a:R[p]={'params':[x.export_text() for x in a.get_editor_property('BlendParameters')],'samples':[x.export_text() for x in a.get_editor_property('SampleData')],'api':[x for x in dir(a) if 'sample' in x]}
c=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(c,'EventGraph');R['crouch_nodes']=[(n.get_name(),str(n.get_node_title()),[(str(p.get_pin_name()),[(x.get_owning_node().get_name(),str(x.get_pin_name()))for x in p.list_connected_pins()]) for p in n.list_all_pins()]) for n in ed.list_all_nodes() if n.get_name().endswith(('CrIA','CrB','DoStand','DoCrouch'))]
R['input_api']={cn:{n:getattr(getattr(unreal,cn),n).__doc__ for n in dir(getattr(unreal,cn)) if 'inject' in n or 'mapping_context' in n} for cn in ['EnhancedInputLocalPlayerSubsystem','EnhancedPlayerInput']}
json.dump(R,open(os.path.join(D,'tfp_blend_probe.json'),'w'),ensure_ascii=False,indent=1)
