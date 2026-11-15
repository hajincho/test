import unreal,os,json,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def node(name):return next((n for n in e.list_all_nodes() if n.get_name()==name),None)
 def fn(name,path):
  n=node(name)
  if not n:n=e.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 def var(name,setter=False,tag=''):
  n=node('TFP_'+('Set' if setter else 'Get')+name+tag)
  if not n:n=(e.add_set_member_variable_node if setter else e.add_get_member_variable_node)(name);n.rename('TFP_'+('Set' if setter else 'Get')+name+tag)
  return n
 for name,default in [('FurinaReserve','120'),('FurinaReloadAmount','0')]:
  if name not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(b)]:e.add_member_variable(name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('int'),default)
 ammo=var('FurinaAmmo');reserve=var('FurinaReserve');amount=var('FurinaReloadAmount');room=fn('TFP_MagRoom','/Script/Engine.KismetMathLibrary:Subtract_IntInt');w(ammo.find_output_pin('FurinaAmmo'),room.find_input_pin('B'));room.find_input_pin('A').set_pin_value('30');transfer=fn('TFP_Transfer','/Script/Engine.KismetMathLibrary:Min');w(room.find_result_pin(),transfer.find_input_pin('A'));w(reserve.find_output_pin('FurinaReserve'),transfer.find_input_pin('B'))
 cache=var('FurinaReloadAmount',True);w(transfer.find_result_pin(),cache.find_input_pin('FurinaReloadAmount'));start=node('M4_SetFurinaReloading');start.find_then_pin().break_pin_links();w(start.find_then_pin(),cache.find_execute_pin());w(cache.find_then_pin(),node('M4_ReloadTimer').find_execute_pin())
 plus=fn('TFP_FilledRounds','/Script/Engine.KismetMathLibrary:Add_IntInt');w(ammo.find_output_pin('FurinaAmmo'),plus.find_input_pin('A'));w(amount.find_output_pin('FurinaReloadAmount'),plus.find_input_pin('B'));fill=node('M4_FillMagazine');w(plus.find_result_pin(),fill.find_input_pin('FurinaAmmo'))
 minus=fn('TFP_ReserveAfter','/Script/Engine.KismetMathLibrary:Subtract_IntInt');w(reserve.find_output_pin('FurinaReserve'),minus.find_input_pin('A'));w(amount.find_output_pin('FurinaReloadAmount'),minus.find_input_pin('B'));setreserve=var('FurinaReserve',True);w(minus.find_result_pin(),setreserve.find_input_pin('FurinaReserve'));fill.find_then_pin().break_pin_links();w(fill.find_then_pin(),setreserve.find_execute_pin());w(setreserve.find_then_pin(),node('M4_ReloadDone').find_execute_pin())
 has=fn('TFP_HasReserve','/Script/Engine.KismetMathLibrary:Greater_IntInt');w(reserve.find_output_pin('FurinaReserve'),has.find_input_pin('A'));has.find_input_pin('B').set_pin_value('0');ready=fn('TFP_ReloadHasAmmo','/Script/Engine.KismetMathLibrary:BooleanAND');w(has.find_result_pin(),ready.find_input_pin('A'));w(node('M4_ReloadReady').find_result_pin(),ready.find_input_pin('B'));w(ready.find_result_pin(),node('M4_ReloadGate').find_input_pin('Condition'))
 del e,ammo,reserve,amount,room,transfer,cache,start,plus,fill,minus,setreserve,has,ready
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['status']=str(b.get_editor_property('status'));R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
 if R['ok']:R['saved']=unreal.EditorAssetLibrary.save_loaded_asset(b,False)
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_reserve.json'),'w'),indent=1)
