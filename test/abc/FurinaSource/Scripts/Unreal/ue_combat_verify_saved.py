"""Read-only verification after the real editor restarts."""
import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'checks':{}}
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');c=unreal.get_default_object(b.generated_class());m=c.character_movement
R['checks']['magazine_30']=c.get_editor_property('FurinaAmmo')==30;R['checks']['crouch_allowed']=m.get_editor_property('nav_agent_props').get_editor_property('can_crouch');R['checks']['crouch_height_58']=abs(m.get_editor_property('crouched_half_height')-58)<.01;R['checks']['diagnostics_removed']=not any(str(n).startswith('Diag') for n in unreal.BlueprintEditorLibrary.list_member_variable_names(b))
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
for h in sub.k2_gather_subobject_data_for_blueprint(b):
 d=lib.get_data(h);n=str(lib.get_variable_name(d));o=lib.get_associated_object(d)
 if n=='FurinaRifle':R['checks']['m4_equipped']='SK_M4A1' in str(o.get_skinned_asset())
 if n=='CameraBoom':R['checks']['camera_fixed_700']=abs(o.get_editor_property('target_arm_length')-700)<.01
notes=[co for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() for co in a.get_components_by_class(unreal.TextRenderComponent)];R['checks']['tutorial_notes_hidden']=all(not co.is_visible() for co in notes);R['note_count']=len(notes)
R['statuses']={p:str(unreal.load_asset(p).get_editor_property('status')) for p in ['/Game/Furina/CR_FurinaSecondary','/Game/Furina/ABP_Furina','/Game/Furina/FP/BP_FurinaHUD','/Game/Furina/FP/BP_FurinaBullet','/Game/Furina/M4/BP_223Case','/Game/Furina/M4/BP_M4Flash']};R['ok']=all(R['checks'].values());json.dump(R,open(os.path.join(D,'combat_fresh_load.json'),'w'),indent=1);print('COMBAT_FRESH_LOAD',R['ok'])
