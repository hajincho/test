import unreal,runpy,os,json
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource';b=unreal.load_asset('/Game/Furina/ABP_Furina')
for name in ('TFPSpeed','TFPDirection','TFPCrouch','TFPGround','TFPHandWalk','TFPHandIdle'):unreal.BlueprintEditorLibrary.change_member_variable_type(b,name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'))
for script in ('ue_tfp_locomotion.py','ue_tfp_hands.py'):runpy.run_path(os.path.join(D,'Scripts','Unreal',script),run_name='__main__')
assert b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR;assert unreal.EditorAssetLibrary.save_loaded_asset(b,False)
