"""Import the supplied M4 and .223 assets; retain weapon animation compatibility."""
import unreal,os,json,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource';DEST='/Game/Furina/M4';R={}
def main():
 e=unreal.EditorAssetLibrary;t=unreal.AssetToolsHelpers.get_asset_tools();ml=unreal.MaterialEditingLibrary
 def imp(path,name,ui):
  task=unreal.AssetImportTask();task.filename=path;task.destination_path=DEST;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.options=ui;t.import_asset_tasks([task]);return unreal.load_asset(DEST+'/'+name)
 ui=unreal.FbxImportUI();ui.import_mesh=True;ui.import_as_skeletal=True;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;ui.import_animations=False;ui.import_materials=False;ui.import_textures=False;ui.create_physics_asset=False;ui.skeleton=unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle_Skeleton')
 sk=imp(os.path.join(D,'FBX','M4','SK_M4A1.fbx'),'SK_M4A1',ui);assert sk;R['mesh']=sk.get_path_name()
 materials={}
 for i in range(1,5):
  name='M_M4_AR'+str(i);p=DEST+'/'+name
  mat=unreal.load_asset(p) if e.does_asset_exist(p) else t.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew())
  ml.delete_all_material_expressions(mat);mat.set_editor_property('used_with_skeletal_mesh',True)
  for suffix,prop,y in [('BaseColor',unreal.MaterialProperty.MP_BASE_COLOR,0),('Metallic',unreal.MaterialProperty.MP_METALLIC,200),('Roughness',unreal.MaterialProperty.MP_ROUGHNESS,400),('Normal',unreal.MaterialProperty.MP_NORMAL,600)]:
   tn='T_M4_AR'+str(i)+'_'+suffix;ptex=DEST+'/'+tn
   tex=unreal.load_asset(ptex) if e.does_asset_exist(ptex) else imp(r'C:\Users\fromj\Downloads\ar15\textures\Ar15_LOW_1_AR'+str(i)+'_'+suffix+'.png',tn,None)
   tex.set_editor_property('srgb',suffix=='BaseColor')
   if suffix=='Normal':tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
   e.save_loaded_asset(tex,False)
   x=ml.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-400,y);x.set_editor_property('texture',tex)
   x.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix=='Normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if suffix=='BaseColor' else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
   ml.connect_material_property(x,'RGB' if suffix in ('BaseColor','Normal') else 'R',prop)
  ml.recompile_material(mat);e.save_loaded_asset(mat,False);materials['AR'+str(i)]=mat
 slots=sk.get_editor_property('materials')
 for index,slot in enumerate(slots):
  key=str(slot.get_editor_property('imported_material_slot_name'));R.setdefault('slots',[]).append(key)
  for k,m in materials.items():
   if k in key:slot.set_editor_property('material_interface',m)
  slots[index]=slot
 sk.set_editor_property('materials',slots);e.save_loaded_asset(sk,False)
 ui=unreal.FbxImportUI();ui.import_mesh=True;ui.import_as_skeletal=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;ui.import_materials=False;ui.import_textures=False;ui.static_mesh_import_data.set_editor_property('auto_generate_collision',True)
 for name in ('SM_223Case','SM_223Projectile'):assert imp(os.path.join(D,'FBX','M4',name+'.fbx'),name,ui)
 for name,color,metal in [('M_Brass',(0.6,.34,.09),.85),('M_Copper',(.62,.23,.09),.8),('M_MuzzleFlash',(15,3,.15),0)]:
  p=DEST+'/'+name;mat=unreal.load_asset(p) if e.does_asset_exist(p) else t.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew());ml.delete_all_material_expressions(mat)
  c=ml.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-300,0);c.set_editor_property('constant',unreal.LinearColor(*color,1));ml.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR if name=='M_MuzzleFlash' else unreal.MaterialProperty.MP_BASE_COLOR)
  if name=='M_MuzzleFlash':mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
  else:
   m=ml.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,200);m.set_editor_property('r',metal);ml.connect_material_property(m,'',unreal.MaterialProperty.MP_METALLIC)
  ml.recompile_material(mat);e.save_loaded_asset(mat,False)
  if name!='M_MuzzleFlash':
   mesh=unreal.load_asset(DEST+('/SM_223Case' if name=='M_Brass' else '/SM_223Projectile'))
   for i in range(mesh.get_num_sections(0)):mesh.set_material(i,mat)
   e.save_loaded_asset(mesh,False)
 R['ok']=True
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'Data','m4_import.json'),'w'),indent=1)
