import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
 b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');n=next(n for n in e.list_all_nodes() if n.get_name()=='TFP_MagRoom');assert n.find_input_pin('A').set_pin_value('30');n=next(n for n in e.list_all_nodes() if n.get_name()=='M4_HasAmmo');n.find_input_pin('B').set_pin_value('0');del e,n
 unreal.BlueprintEditorLibrary.compile_blueprint(b)
 c=unreal.get_default_object(b.generated_class());cm=c.character_movement;R={'nav':str(cm.get_editor_property('nav_agent_props')),'crouch_height':cm.crouched_half_height,'status':str(b.get_editor_property('status'))};json.dump(R,open(os.path.join(D,'tfp_cdo.json'),'w'),indent=1)
main()
