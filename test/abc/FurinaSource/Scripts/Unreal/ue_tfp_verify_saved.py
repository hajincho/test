import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'checks':{},'statuses':{}}
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');c=unreal.get_default_object(b.generated_class());R['checks']['ammo_30_120']=c.get_editor_property('FurinaAmmo')==30 and c.get_editor_property('FurinaReserve')==120;R['checks']['crouch_allowed']=c.character_movement.get_editor_property('nav_agent_props').get_editor_property('can_crouch');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');R['checks']['no_test_helpers']=not any(n.get_name().startswith('TFPTest_') for n in e.list_all_nodes());R['checks']['zero_50m']=next(n for n in e.list_all_nodes() if n.get_name()=='K2Node_FPF_Far').find_input_pin('B').get_pin_value()=='5000'
a=unreal.load_asset('/Game/Furina/ABP_Furina');R['checks']['cache_real']=all('PinCategory="real"' in unreal.BlueprintEditorLibrary.get_member_variable_type(a,k).export_text() for k in ('TFPSpeed','TFPDirection','TFPCrouch','TFPGround','TFPHandWalk','TFPHandIdle'))
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
for h in sub.k2_gather_subobject_data_for_blueprint(b):
 d=lib.get_data(h);n=str(lib.get_variable_name(d));o=lib.get_associated_object(d)
 if n=='CameraBoom':R['checks']['arm_469']=abs(o.target_arm_length-469)<.01
for p in ['/Game/Furina/CR_FurinaSecondary','/Game/Furina/ABP_Furina','/Game/Furina/FP/BP_FurinaHUD','/Game/Furina/FP/BP_FurinaBullet','/Game/Furina/M4/BP_223Case']:R['statuses'][p]=str(unreal.load_asset(p).get_editor_property('status'))
actors=[x for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(x,unreal.Character) and x.get_class().get_name().startswith('ThirdPersonCharacter_BP')];R['checks']['placed_character_can_crouch']=bool(actors) and all(x.character_movement.get_editor_property('nav_agent_props').get_editor_property('can_crouch') for x in actors);R['checks']['hud_surface_material']=unreal.load_asset('/Game/Furina/UI/M_M4HUDFrame').get_editor_property('material_domain')==unreal.MaterialDomain.MD_SURFACE
R['ok']=all(R['checks'].values());json.dump(R,open(os.path.join(D,'tfp_fresh_load.json'),'w'),indent=1)

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
