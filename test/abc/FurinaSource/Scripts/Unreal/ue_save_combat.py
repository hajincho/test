import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'saved':[],'failed':[],'hidden_notes':[]}
for p in ['/Game/Furina/CR_FurinaSecondary','/Game/Furina/ABP_Furina','/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP','/Game/Furina/FP/BP_FurinaHUD','/Game/Furina/FP/BP_FurinaBullet']:
 a=unreal.load_asset(p)
 if unreal.EditorAssetLibrary.save_loaded_asset(a,False):R['saved'].append(p)
 else:R['failed'].append(p)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 for c in a.get_components_by_class(unreal.TextRenderComponent):
  if str(c.get_editor_property('text')):
   a.modify();c.modify();c.set_visibility(False);c.set_hidden_in_game(True);R['hidden_notes'].append(a.get_name())
 if isinstance(a,unreal.Character):
  for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
   if c.get_name()=='FurinaRifle':a.modify();c.modify();c.set_skinned_asset_and_update(unreal.load_asset('/Game/Furina/M4/SK_M4A1'))
if unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/3DPlatformerGameBundle/Levels/ExampleLevel'):R['saved'].append('ExampleLevel')
else:R['failed'].append('ExampleLevel')
R['ok']=not R['failed'];json.dump(R,open(os.path.join(D,'combat_save.json'),'w'),indent=1)
