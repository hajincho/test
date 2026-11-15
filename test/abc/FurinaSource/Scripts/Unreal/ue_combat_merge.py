"""Merge generated stance nodes using the public Blueprint graph API. Stage first; save separately."""
import unreal,re,os,json,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={'added':[],'warnings':[]}
def main():
 bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
 def merge(filename):
  text=open(os.path.join(D,filename),encoding='utf-8-sig').read(); records=[]; pins={}; objs={n.get_name():n for n in ed.list_all_nodes()}
  for block in re.findall(r'Begin Object .*?\nEnd Object',text,re.S):
   name=re.search(r'Name="([^"]+)"',block)[1]; cls=re.search(r'Class=([^ ]+)',block)[1]; records.append((name,cls,block))
   for line in block.splitlines():
    if 'CustomProperties Pin' not in line:continue
    pid=re.search(r'PinId=(\w+)',line)[1]; pn=re.search(r'PinName="([^"]+)"',line)[1]; pins[pid]=(name,pn,line)
  for name,cls,block in records:
   if name in objs:continue
   if cls.endswith('K2Node_CallFunction'):
    fn=re.search(r'FunctionReference=\(MemberParent="[^"]*\x27([^\x27]+)\x27",MemberName="([^"]+)"',block)
    assert fn, name
    n=ed.add_call_function_node(fn[1]+':'+fn[2])
    if not n and fn[2]=='IsCrouching':n=ed.add_call_function_node('/Script/Engine.NavMovementComponent:IsCrouching')
   elif cls.endswith('K2Node_VariableGet') or cls.endswith('K2Node_VariableSet'):
    member=re.search(r'VariableReference=.*?MemberName="([^"]+)"',block)[1]
    parent=re.search(r'VariableReference=.*?MemberParent="[^\x27]*\x27([^\x27]+)',block)
    method=ed.add_get_member_variable_node if cls.endswith('Get') else ed.add_set_member_variable_node
    n=method(member,parent[1] if parent else '')
   elif cls.endswith('K2Node_IfThenElse'):n=ed.add_branch_node()
   elif cls.endswith('K2Node_Self'):
    n=next(n for n in ed.list_all_nodes() if n.get_class().get_name()=='K2Node_Self');objs[name]=n;continue
   elif cls.endswith('K2Node_EnhancedInputAction'):
    n=ed.create_node_from_name('Input|EnhancedActionEvents|IA_FurinaCrouch',unreal.Vector2D(0,0),[])
   else:raise RuntimeError('Unsupported missing '+name+' '+cls)
   assert n,name;n.rename(name);objs[name]=n;R['added'].append(name)
  # Clear only pins owned by these generated blocks; preserve unrelated event graphs.
  for pid,(name,pn,line) in pins.items():
   n=objs[name];p=n.find_output_pin(pn) if 'EGPD_Output' in line else n.find_input_pin(pn)
   if not p.is_valid() and n.get_class().get_name()=='K2Node_ExecutionSequence':
    while not p.is_valid():assert ed.add_node_pin(n);p=n.find_output_pin(pn)
   if not p.is_valid() and ('bHidden=True' in line or pn=='bClientSimulation'):continue
   assert p.is_valid(),name+'.'+pn
   p.break_pin_links()
   default=re.search(r'DefaultValue="((?:\\.|[^"\\])*)"',line)
   if default:
    val=default[1].replace('\\"','"')
    if not p.set_pin_value(val):R['warnings'].append(name+'.'+pn+' default '+val)
  for pid,(name,pn,line) in pins.items():
   if 'EGPD_Output' not in line:continue
   linked=re.search(r'LinkedTo=\(([^)]*)\)',line)
   if not linked:continue
   for target,tid in re.findall(r'(\w+) (\w+),',linked[1]):
    tn,tp,_=pins[tid]
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(objs[name].find_output_pin(pn),objs[tn].find_input_pin(tp)),name+'.'+pn+' -> '+tn+'.'+tp
  # New wildcard math nodes acquire their numeric type when linked. Apply their
  # literals after linking so constants such as 0.5 are not reset to zero.
  for pid,(name,pn,line) in pins.items():
   if 'EGPD_Output' in line:continue
   p=objs[name].find_input_pin(pn)
   default=re.search(r'DefaultValue="((?:\\.|[^"\\])*)"',line)
   if p.is_valid() and default and not p.list_connected_pins():
    assert p.set_pin_value(default[1].replace('\\"','"')),name+'.'+pn
  del objs,records,pins
 merge('fp_aim_tick.t3d');merge('fp_fire_char.t3d')
 # Fixed third-person zoom at the project's current 700 cm distance; collision retraction remains enabled.
 nodes={n.get_name():n for n in ed.list_all_nodes()}
 nodes['K2Node_EnhancedInputAction_Zoom'].find_output_pin('Triggered').break_pin_links()
 # Disable diagnostic PrintString overlays, retaining their log output.
 for n in ed.list_all_nodes():
  p=n.find_input_pin('bPrintToScreen')
  if p.is_valid():p.set_pin_value('false')
 del nodes,ed
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 R['status']=str(bp.get_editor_property('status'))
 R['errors']=[]
 ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph')
 R['errors']=[str(n.get_node_title()) for n in ed.list_nodes_with_errors()]
 R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_merge.json'),'w'),indent=1)



