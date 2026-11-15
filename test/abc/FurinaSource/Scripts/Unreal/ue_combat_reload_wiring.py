import unreal,json
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');R={'life':unreal.get_default_object(b.generated_class()).get_editor_property('initial_life_span'),'nodes':{}}
for n in e.list_all_nodes():
 if n.get_name() in ('K2Node_FP_ReloadRifle','K2Node_FP_ReloadMontage','K2Node_FPF_Bolt','K2Node_FPF_FireRifle','K2Node_FPF_Spawn'):
  R['nodes'][n.get_name()]={'title':str(n.get_node_title()),'inputs':[(str(p.get_pin_name()),p.get_pin_value(),[(p2.get_owning_node().get_name(),str(p2.get_owning_node().get_node_title())) for p2 in p.list_connected_pins()]) for p in n.list_input_pins()]}
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_reload_wiring.json','w'),indent=1,ensure_ascii=False)
