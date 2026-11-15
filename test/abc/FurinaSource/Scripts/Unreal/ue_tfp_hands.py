"""Cache upper-body blend weights from real speed; TFP clips use their own curves."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 b=unreal.load_asset('/Game/Furina/ABP_Furina');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def node(name):return next((n for n in e.list_all_nodes() if n.get_name()==name),None)
 def fn(name,path):
  n=node(name)
  if not n:n=e.add_call_function_node(path);n.rename(name)
  return n
 names=[str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(b)]
 for name in ('TFPHandWalk','TFPHandIdle'):
  if name not in names:e.add_member_variable(name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'),'1')
 prev=node('CacheTFPGround').find_then_pin();existing=node('CacheTFPHandIdle');old=list(existing.find_then_pin().list_connected_pins()) if existing else list(prev.list_connected_pins());prev.break_pin_links()
 for var,lo,hi in [('TFPHandWalk',120,600),('TFPHandIdle',0,20)]:
  speed=e.add_get_member_variable_node('TFPSpeed');map=fn(var+'Range','/Script/Engine.KismetMathLibrary:MapRangeClamped');w(speed.find_output_pin('TFPSpeed'),map.find_input_pin('Value'))
  for pin,val in [('InRangeA',lo),('InRangeB',hi),('OutRangeA',1),('OutRangeB',0)]:map.find_input_pin(pin).set_pin_value(str(val))
  set=node('Cache'+var)
  if not set:set=e.add_set_member_variable_node(var);set.rename('Cache'+var)
  w(prev,set.find_execute_pin());w(map.find_result_pin(),set.find_input_pin(var));prev=set.find_then_pin()
 for p in old:
  if not p.get_owning_node().get_name().startswith('CacheTFPHand'):w(prev,p)
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'AnimGraph')
 for name,var in [('AnimGraphNode_TwoWayBlend_FPWalk','TFPHandWalk'),('AnimGraphNode_TwoWayBlend_FPIdle','TFPHandIdle')]:
  n=next(n for n in ed.list_all_nodes() if n.get_name()==name);v=n.get_editor_property('blend_node');assert v.import_text(v.export_text().replace('AlphaInputType=Curve','AlphaInputType=Float'));n.set_editor_property('blend_node',v)
  opts=list(n.get_editor_property('show_pin_for_properties'))
  for i,o in enumerate(opts):
   if str(o.get_editor_property('PropertyName'))=='Alpha':o.set_editor_property('bShowPin',True);opts[i]=o
  n.set_editor_property('show_pin_for_properties',opts);oldf=n.get_editor_property('initial_update_function').copy();tmp=oldf.copy();tmp.import_text('(MemberName="FurinaReconstructTemporary")');n.set_editor_property('initial_update_function',tmp);n.set_editor_property('initial_update_function',oldf);get=ed.add_get_member_variable_node(var);w(get.find_output_pin(var),n.find_input_pin('Alpha'))
 del e,ed,n,v,opts,get,speed,map,set,prev,existing,old
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['status']=str(b.get_editor_property('status'));R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_hands.json'),'w'),indent=1)
