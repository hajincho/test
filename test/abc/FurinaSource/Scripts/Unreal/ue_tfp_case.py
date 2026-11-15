"""Explicit local ejection vector avoids UE promoted multiply dropping scalar defaults."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/M4/BP_223Case');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph');nodes={n.get_name():n for n in ed.list_all_nodes()}
 def w(a,b):assert a.is_valid() and b.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
 xf=nodes.get('TFPCaseTransform')
 if not xf:xf=ed.add_call_function_node('/Script/Engine.Actor:GetTransform');xf.rename('TFPCaseTransform')
 direction=nodes.get('TFPCaseDirection')
 if not direction:direction=ed.add_call_function_node('/Script/Engine.KismetMathLibrary:TransformDirection');direction.rename('TFPCaseDirection')
 direction.find_input_pin('Direction').set_pin_value('-140,180,130');w(xf.find_result_pin(),direction.find_input_pin('T'));w(direction.find_result_pin(),nodes['CaseVelocity'].find_input_pin('NewVel'))
 S=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);L=unreal.SubobjectDataBlueprintFunctionLibrary
 for h in S.k2_gather_subobject_data_for_blueprint(bp):
  if str(L.get_variable_name(L.get_data(h)))=='FXMesh':
   body=L.get_associated_object(L.get_data(h));body.set_editor_property('relative_scale3d',unreal.Vector(1.35,1.35,1.35));body.set_editor_property('owner_no_see',False);body.set_editor_property('only_owner_see',False);body.set_editor_property('hidden_in_game',False);body.set_editor_property('cast_shadow',False);body.set_editor_property('min_draw_distance',0.);body.set_editor_property('ld_max_draw_distance',0.);body.set_all_use_ccd(True)
 del ed,nodes,xf,direction
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);unreal.get_default_object(bp.generated_class()).set_editor_property('initial_life_span',6.0);R['status']=str(bp.get_editor_property('status'))
 m=unreal.load_asset('/Game/Furina/M4/M_Brass');ml=unreal.MaterialEditingLibrary
 em=ml.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-300,600);em.set_editor_property('constant',unreal.LinearColor(.12,.065,.015,1));ml.connect_material_property(em,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);rough=ml.create_material_expression(m,unreal.MaterialExpressionConstant,-300,800);rough.set_editor_property('r',.28);ml.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);ml.recompile_material(m)
 R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_case.json'),'w'),indent=1)

