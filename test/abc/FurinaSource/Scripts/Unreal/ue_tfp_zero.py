import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 B=json.load(open(os.path.join(D,'ballistics.json')));b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');n={a.get_name():a for a in e.list_all_nodes()}
 for name,pin,value in [('Far','B',5000),('Lift','B',B['zero_elev_rad']),('RecV0','Min',.46*.88),('RecV0','Max',.46*1.12),('RecH0','Min',-.18),('RecH0','Max',.22),('AdsGain','A',1.8)]:assert n['K2Node_FPF_'+name].find_input_pin(pin).set_pin_value(str(value)),name
 for pin in ('A','B'):assert unreal.BlueprintGraphPinLibrary.try_create_connection(n['K2Node_FPF_End'].find_result_pin(),n['K2Node_FPF_AimPt'].find_input_pin(pin))
 del e,n
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['character_status']=str(b.get_editor_property('status'))
 bullet=unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet');s=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);l=unreal.SubobjectDataBlueprintFunctionLibrary
 for h in s.k2_gather_subobject_data_for_blueprint(bullet):
  name=str(l.get_variable_name(l.get_data(h)));c=l.get_associated_object(l.get_data(h))
  if name=='Ballistics':c.set_editor_property('force_sub_stepping',True);c.set_editor_property('max_simulation_time_step',.004);c.set_editor_property('max_simulation_iterations',16)
  if name=='Bullet':c.set_editor_property('sphere_radius',.285)
 unreal.BlueprintEditorLibrary.compile_blueprint(bullet);R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_zero.json'),'w'),indent=1)
