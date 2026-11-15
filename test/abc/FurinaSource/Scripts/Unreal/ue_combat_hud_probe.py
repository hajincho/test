import unreal,json,traceback,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
 R['actions']=[s for s in ed.list_available_nodes([]) if s.endswith('CastToCharacter')]
 R['nodes']=[(n.get_name(),str(n.get_node_title())) for n in ed.list_all_nodes()];R['eventpins']=[str(p.get_pin_name()) for p in ed.find_event_node('ReceiveDrawHUD').list_all_pins()]
 cast=ed.create_node_from_name(R['actions'][0],unreal.Vector2D(0,1000),[]);R['castpins']=[str(p.get_pin_name()) for p in cast.list_all_pins()];R['castclass']=str(cast.get_editor_property('target_type'));cast.rename('M4_AmmoCast')
 target=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class();assert ed.retarget_node_class(cast,cast.get_editor_property('target_type'),target)
 R['after']=[str(p.get_pin_name()) for p in cast.list_all_pins()]
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_hud_probe.json'),'w'),indent=1,ensure_ascii=False)


