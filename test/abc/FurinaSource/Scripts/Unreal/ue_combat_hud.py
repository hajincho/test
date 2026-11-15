import unreal,json,traceback,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'EventGraph');target=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class()
 def wire(a,b):assert a.is_valid() and b.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,b)
 def fn(name,path):
  n=next((n for n in ed.list_all_nodes() if n.get_name()=='M4HUD_'+name),None)
  if not n:n=ed.add_call_function_node(path);assert n,path;n.rename('M4HUD_'+name)
  return n
 cast=next((n for n in ed.list_all_nodes() if n.get_name()=='M4HUD_Cast'),None)
 if not cast:
  cast=ed.create_node_from_name('Utilities|Casting|CastToCharacter',unreal.Vector2D(0,1000),[]);assert cast;cast.rename('M4HUD_Cast');assert ed.retarget_node_class(cast,unreal.Character,target)
 result=next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
 own=fn('Pawn','/Script/Engine.HUD:GetOwningPawn');wire(own.find_result_pin(),cast.find_input_pin('Object'))
 ammo=next((n for n in ed.list_all_nodes() if n.get_name()=='M4HUD_Ammo'),None)
 if not ammo:ammo=ed.add_get_member_variable_node('FurinaAmmo',target.get_path_name());assert ammo;ammo.rename('M4HUD_Ammo')
 wire(result,ammo.find_self_pin());convert=fn('Number','/Script/Engine.KismetStringLibrary:Conv_IntToString');wire(ammo.find_output_pin('FurinaAmmo'),convert.find_input_pin('InInt'))
 text=fn('Label','/Script/Engine.KismetStringLibrary:Concat_StrStr');wire(convert.find_result_pin(),text.find_input_pin('A'));text.find_input_pin('B').set_pin_value(' / 30')
 draw=fn('DrawAmmo','/Script/Engine.HUD:DrawText');wire(text.find_result_pin(),draw.find_input_pin('Text'));draw.find_input_pin('TextColor').set_pin_value('(R=1,G=1,B=1,A=1)');draw.find_input_pin('Scale').set_pin_value('1.2')
 event=ed.find_event_node('ReceiveDrawHUD');old=[p for p in event.find_then_pin().list_connected_pins() if p.get_owning_node()!=cast];event.find_then_pin().break_pin_links();wire(event.find_then_pin(),cast.find_execute_pin());wire(cast.find_then_pin(),draw.find_execute_pin())
 for p in old:wire(draw.find_then_pin(),p);wire(cast.find_output_pin('CastFailed'),p)
 for axis,offset in [('X','150'),('Y','55')]:
  sub=fn('Screen'+axis,'/Script/Engine.KismetMathLibrary:Subtract_IntInt');wire(event.find_output_pin('Size'+axis),sub.find_input_pin('A'));sub.find_input_pin('B').set_pin_value(offset);wire(sub.find_result_pin(),draw.find_input_pin('Screen'+axis))
 del ed,cast,result,own,ammo,convert,text,draw,event,old,sub,p
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);R['status']=str(bp.get_editor_property('status'));R['ok']=bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_hud.json'),'w'),indent=1)
