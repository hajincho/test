import unreal,runpy,os,json
ROOT=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
u=unreal.FbxImportUI();u.import_mesh=True;u.import_as_skeletal=True;u.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;u.import_animations=False;u.import_materials=False;u.import_textures=False;u.create_physics_asset=False;u.skeleton=unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle_Skeleton')
t=unreal.AssetImportTask();t.filename=os.path.join(ROOT,'FBX','M4','SK_M4A1.fbx');t.destination_path='/Game/Furina/M4';t.destination_name='SK_M4A1';t.automated=True;t.save=True;t.replace_existing=True;t.options=u;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
for script in ('ue_build_cr.py','ue_attach_m4.py','ue_validate_combat.py'):runpy.run_path(os.path.join(ROOT,'Scripts','Unreal',script),run_name='__main__')
