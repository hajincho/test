import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/ABP_Furina');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'AnimGraph')
 n=next(n for n in unreal.AnimationLibrary.get_nodes_of_class(bp,unreal.AnimGraphNode_ModifyCurve,True) if n.get_name().endswith('ViewState'))
 v=n.get_editor_property('node');text=v.export_text()
 if 'Crouch' not in text:
  text=text.replace('CurveValues=(0.000000)','CurveValues=(0.000000,0.000000)').replace('CurveNames=("ViewTP")','CurveNames=("ViewTP","Crouch")')
  assert v.import_text(text);n.set_editor_property('node',v)
 old=n.get_editor_property('initial_update_function').copy();tmp=old.copy()
 tmp.import_text('(MemberName="FurinaReconstructTemporary")')
 n.set_editor_property('initial_update_function',tmp)
 n.set_editor_property('initial_update_function',old)
 R['pins']=[str(p.get_pin_name()) for p in n.list_all_pins()]
 def call(name,path):
  a=next((x for x in ed.list_all_nodes() if x.get_name()==name),None)
  if not a:a=ed.add_call_function_node(path);assert a,path;a.rename(name)
  return a
 own=call('FurinaCrouchOwner','/Script/Engine.AnimInstance:TryGetPawnOwner');mov=call('FurinaCrouchMovement','/Script/Engine.Pawn:GetMovementComponent');cr=call('FurinaCrouchActual','/Script/Engine.NavMovementComponent:IsCrouching');cv=call('FurinaCrouchFloat','/Script/Engine.KismetMathLibrary:Conv_BoolToDouble')
 for a,b in [(own.find_result_pin(),mov.find_self_pin()),(mov.find_result_pin(),cr.find_self_pin()),(cr.find_result_pin(),cv.find_input_pin('InBool')),(cv.find_result_pin(),n.find_input_pin('CurveValues_1'))]:assert unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
 del ed,n,v,own,mov,cr,cv,a,b
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['status']=str(bp.get_editor_property('status'));R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_crouch_curve.json'),'w'),indent=1)
