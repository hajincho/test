import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
 hs={str(lib.get_variable_name(lib.get_data(h))):h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
 gun=lib.get_associated_object(lib.get_data(hs['FurinaRifle']));gun.set_skinned_asset_and_update(unreal.load_asset('/Game/Furina/M4/SK_M4A1'));R['gun']=str(gun.get_skinned_asset())
 boom=lib.get_associated_object(lib.get_data(hs['CameraBoom']));boom.set_editor_property('target_arm_length',700.)
 del gun,boom,hs
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['status']=str(bp.get_editor_property('status'))
 bullet=unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet');hs={str(lib.get_variable_name(lib.get_data(h))):h for h in sub.k2_gather_subobject_data_for_blueprint(bullet)}
 movement=lib.get_associated_object(lib.get_data(hs['Ballistics']));movement.set_editor_property('initial_speed',91000.)
 if 'ProjectileVisual' not in hs:
  h,err=sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['Bullet'],new_class=unreal.StaticMeshComponent,blueprint_context=bullet));sub.rename_subobject(h,unreal.Text('ProjectileVisual'));hs['ProjectileVisual']=h
 v=lib.get_associated_object(lib.get_data(hs['ProjectileVisual']));v.set_static_mesh(unreal.load_asset('/Game/Furina/M4/SM_223Projectile'));v.set_collision_profile_name('NoCollision');v.set_editor_property('relative_rotation',unreal.Rotator(yaw=-90));del movement,v,hs
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bullet,'EventGraph');drag=next(n for n in ed.list_all_nodes() if n.get_name().endswith('_Drag')) if False else None
 # Patch the existing air-drag literal using generated node names, without replacing hit/collision logic.
 B=json.load(open(os.path.join(D,'ballistics.json')))
 for n in ed.list_all_nodes():
  if n.get_name().endswith('_Kv'):
   p=n.find_input_pin('B')
   if p.is_valid():p.set_pin_value(str(B['k_per_cm']))
 R['bullet_nodes']=[n.get_name() for n in ed.list_all_nodes()]
 del ed,drag
 unreal.BlueprintEditorLibrary.compile_blueprint(bullet);R['bullet_status']=str(bullet.get_editor_property('status'));R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR and bullet.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'m4_attach.json'),'w'),indent=1)

