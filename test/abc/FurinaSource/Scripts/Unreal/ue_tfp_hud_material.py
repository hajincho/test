"""Import the supplied HUD unchanged; hide its printed ammo digits in the runtime material."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();M=unreal.MaterialEditingLibrary;dest='/Game/Furina/UI';tp=dest+'/T_M4HUDFrame'
 if not E.does_asset_exist(tp):
  task=unreal.AssetImportTask();task.filename=r'C:\Users\fromj\Downloads\미래형 M4A1 무기 HUD 프레임.png';task.destination_path=dest;task.destination_name='T_M4HUDFrame';task.automated=True;task.save=True;T.import_asset_tasks([task])
 tex=unreal.load_asset(tp);assert tex;tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON);tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI);tex.set_editor_property('never_stream',True);E.save_loaded_asset(tex,False)
 p=dest+'/M_M4HUDFrame';mat=unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset('M_M4HUDFrame',dest,unreal.Material,unreal.MaterialFactoryNew());M.delete_all_material_expressions(mat);mat.set_editor_property('material_domain',unreal.MaterialDomain.MD_SURFACE);mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
 sample=M.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-600,0);sample.set_editor_property('texture',tex);uv=M.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-600,200);custom=M.create_material_expression(mat,unreal.MaterialExpressionCustom,-300,0);custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
 inputs=[]
 for n in ('Alpha','UV'):
  i=unreal.CustomInput();i.set_editor_property('input_name',n);inputs.append(i)
 custom.set_editor_property('inputs',inputs);custom.set_editor_property('code','float box = step(0.07,UV.x)*step(UV.x,0.33)*step(0.67,UV.y)*step(UV.y,0.86); return Alpha*(1-box);')
 assert M.connect_material_expressions(sample,'A',custom,'Alpha')
 assert M.connect_material_expressions(uv,'',custom,'UV')
 assert M.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 assert M.connect_material_property(custom,'',unreal.MaterialProperty.MP_OPACITY)
 M.recompile_material(mat);E.save_loaded_asset(mat,False);R['ok']=True
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_hud_material.json'),'w'),indent=1)
