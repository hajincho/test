import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
 b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 temps=[n for n in e.list_all_nodes() if str(n.get_node_title())=='FurinaInspectFire' or any(n.find_input_pin(v).is_valid() for v in ('DiagAim','DiagCanFire','DiagShoulder','DiagReady'))]
 if temps:e.remove_nodes(temps)
 for name in ('DiagAim','DiagCanFire','DiagShoulder','DiagReady'):
  if name in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(b)]:e.remove_member_variable(name)
 n=next(n for n in e.list_all_nodes() if n.get_name()=='M4_CasePoint');assert n.find_input_pin('Location').set_pin_value('-2,-6.75879,4.52615')
 del e,n,temps
 unreal.BlueprintEditorLibrary.compile_blueprint(b);assert b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR;assert unreal.EditorAssetLibrary.save_loaded_asset(b,False)
 case=unreal.load_asset('/Game/Furina/M4/BP_223Case');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(case,'EventGraph');n=next(n for n in e.list_all_nodes() if n.get_name()=='CaseRightSpeed');assert n.find_input_pin('B').set_pin_value('-220');del e,n
 unreal.BlueprintEditorLibrary.compile_blueprint(case);assert unreal.EditorAssetLibrary.save_loaded_asset(case,False)
 json.dump({'ok':True,'character_status':str(b.get_editor_property('status')),'case_status':str(case.get_editor_property('status'))},open(os.path.join(D,'combat_final_save.json'),'w'))
main()
