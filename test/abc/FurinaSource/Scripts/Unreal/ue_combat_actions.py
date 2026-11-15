import unreal,json
bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
R={'actions':[n for n in ed.list_available_nodes([]) if any(x in n.lower() for x in ('ia_furinacrouch','sequence','self'))]}
a=unreal.load_asset('/Game/Furina/ABP_Furina');ae=unreal.BlueprintGraphEditor.get_graph_editor_by_name(a,'AnimGraph')
R['animactions']=[n for n in ae.list_available_nodes([]) if 'modify' in n.lower()]
R['animapi']={n:getattr(unreal.AnimationLibrary,n).__doc__ for n in dir(unreal.AnimationLibrary) if any(x in n for x in ('node','pin'))}
R['pinapi']={n:getattr(unreal.BlueprintGraphPin,n).__doc__ for n in dir(unreal.BlueprintGraphPin) if any(x in n for x in ('value','name','type','direction'))}
R['rigpins']=[(n.get_name(), str(n.get_class())) for n in unreal.load_asset('/Game/Furina/CR_FurinaSecondary').get_controller().get_graph().get_nodes() if n.get_name() in ('TpD','LBack','CrouchC')]
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_actions.json','w'),indent=1)

