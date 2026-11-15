"""Supplied M4 frame with live 30/120 counts, plus targeted demo-instruction cleanup."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 E=unreal.EditorAssetLibrary;b=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph');target=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class()
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def node(name):return next((n for n in e.list_all_nodes() if n.get_name()==name),None)
 def fn(name,path):
  n=node(name)
  if not n:n=e.add_call_function_node(path);assert n,path;n.rename(name)
  return n
 def math(name,func,a=None,b=None):
  n=fn(name,'/Script/Engine.KismetMathLibrary:'+func)
  for k,v in [('A',a),('B',b)]:
   if v is not None:
    if isinstance(v,(int,float)):
     lit=fn(name+'Literal'+k,'/Script/Engine.KismetSystemLibrary:MakeLiteralDouble');lit.find_input_pin('Value').set_pin_value(str(v));w(lit.find_result_pin(),n.find_input_pin(k))
    else:w(v,n.find_input_pin(k))
  return n.find_result_pin()
 event=e.find_event_node('ReceiveDrawHUD');sx=fn('TFPHUD_ScreenXFloat','/Script/Engine.KismetMathLibrary:Conv_IntToDouble');sy=fn('TFPHUD_ScreenYFloat','/Script/Engine.KismetMathLibrary:Conv_IntToDouble');w(event.find_output_pin('SizeX'),sx.find_input_pin('InInt'));w(event.find_output_pin('SizeY'),sy.find_input_pin('InInt'));width=math('TFPHUD_Width','Multiply_DoubleDouble',sx.find_result_pin(),.30);cl=fn('TFPHUD_WidthClamp','/Script/Engine.KismetMathLibrary:FClamp');w(width,cl.find_input_pin('Value'));cl.find_input_pin('Min').set_pin_value('360');cl.find_input_pin('Max').set_pin_value('540');width=cl.find_result_pin();height=math('TFPHUD_Height','Divide_DoubleDouble',width,3)
 right=math('TFPHUD_Right','Subtract_DoubleDouble',sx.find_result_pin(),24);bottom=math('TFPHUD_Bottom','Subtract_DoubleDouble',sy.find_result_pin(),24);x=math('TFPHUD_X','Subtract_DoubleDouble',right,width);y=math('TFPHUD_Y','Subtract_DoubleDouble',bottom,height)
 draw=fn('TFPHUD_Frame','/Script/Engine.HUD:DrawMaterial');assert draw.find_input_pin('Material').set_pin_value('/Game/Furina/UI/M_M4HUDFrame.M_M4HUDFrame')
 for pin,value in [('ScreenX',x),('ScreenY',y),('ScreenW',width),('ScreenH',height)]:w(value,draw.find_input_pin(pin))
 for pin,value in [('MaterialU','0'),('MaterialV','0'),('MaterialUWidth','1'),('MaterialVHeight','1'),('Scale','1')]:assert draw.find_input_pin(pin).set_pin_value(value)
 ammo=node('M4HUD_DrawAmmo');cast=node('M4HUD_Cast');cast.find_then_pin().break_pin_links();w(cast.find_then_pin(),draw.find_execute_pin());w(draw.find_then_pin(),ammo.find_execute_pin())
 nx=math('TFPHUD_NumX','Add_DoubleDouble',x,math('TFPHUD_NumXOffset','Multiply_DoubleDouble',width,.085));ny=math('TFPHUD_NumY','Add_DoubleDouble',y,math('TFPHUD_NumYOffset','Multiply_DoubleDouble',height,.69));w(nx,ammo.find_input_pin('ScreenX'));w(ny,ammo.find_input_pin('ScreenY'))
 font=unreal.load_asset('/Game/3DPlatformerGameBundle/Fonts/Kenvector_Future_Font');font_size=font.get_editor_property('legacy_font_size') or 20;scale=math('TFPHUD_FontScale','Multiply_DoubleDouble',width,23/(540*font_size));w(scale,ammo.find_input_pin('Scale'));ammo.find_input_pin('Font').set_pin_value(font.get_path_name())
 reserve=node('TFPHUD_Reserve')
 if not reserve:reserve=e.add_get_member_variable_node('FurinaReserve',target.get_path_name());reserve.rename('TFPHUD_Reserve')
 result=next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'));w(result,reserve.find_self_pin());number=fn('TFPHUD_ReserveString','/Script/Engine.KismetStringLibrary:Conv_IntToString');w(reserve.find_output_pin('FurinaReserve'),number.find_input_pin('InInt'));label=node('M4HUD_Label');label.find_input_pin('B').set_pin_value('/');tail=fn('TFPHUD_LiveAmmo','/Script/Engine.KismetStringLibrary:Concat_StrStr');w(label.find_result_pin(),tail.find_input_pin('A'));w(number.find_result_pin(),tail.find_input_pin('B'));w(tail.find_result_pin(),ammo.find_input_pin('Text'))
 # Keep guidance objects alive for the platformer components, but collapse their visual widgets.
 begin=e.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(b,'ReceiveBeginPlay',unreal.IntPoint(0,0));timer=fn('TFPHUD_CleanupTimer','/Script/Engine.KismetSystemLibrary:K2_SetTimer');timer.find_input_pin('FunctionName').set_pin_value('FurinaHideDemoGuides');timer.find_input_pin('Time').set_pin_value('.5');timer.find_input_pin('bLooping').set_pin_value('true');w(begin.find_then_pin(),timer.find_execute_pin())
 cleanup=next((n for n in e.list_all_nodes() if str(n.get_node_title())=='FurinaHideDemoGuides'),None)
 if not cleanup:cleanup=e.add_custom_event_node('FurinaHideDemoGuides')
 prev=cleanup.find_then_pin();classes=['/Game/3DPlatformerGameBundle/Widgets/Guide_Widget_WBP','/Game/3DPlatformerGameBundle/Widgets/GrindRailGuideWidgetBP/Guide_Widget_WBP','/Game/3DPlatformerGameBundle/Widgets/HomingAttackGuideWidgetBP/Guide_Widget_WBP','/Game/3DPlatformerGameBundle/Widgets/JumpPadGuideWidgetBP/Guide_Widget_WBP']
 for i,path in enumerate(classes):
  if not E.does_asset_exist(path):continue
  get=fn('TFPHUD_Guides'+str(i),'/Script/UMG.WidgetBlueprintLibrary:GetAllWidgetsOfClass');get.find_input_pin('WidgetClass').set_pin_value(path+'.Guide_Widget_WBP_C');get.find_input_pin('TopLevelOnly').set_pin_value('false')
  loop=node('TFPHUD_Loop'+str(i))
  if not loop:loop=e.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop');assert loop;loop.rename('TFPHUD_Loop'+str(i))
  w(prev,get.find_execute_pin());w(get.find_then_pin(),loop.find_input_pin('Exec'));w(get.find_output_pin('FoundWidgets'),loop.find_input_pin('Array'));hide=fn('TFPHUD_Hide'+str(i),'/Script/UMG.Widget:SetVisibility');hide.find_input_pin('InVisibility').set_pin_value('Collapsed');w(loop.find_output_pin('Array Element'),hide.find_self_pin());w(loop.find_output_pin('LoopBody'),hide.find_execute_pin());prev=loop.find_output_pin('Completed')
 get=fn('TFPHUD_WorldNotes','/Script/Engine.GameplayStatics:GetAllActorsOfClass');get.find_input_pin('ActorClass').set_pin_value('/Script/Engine.TextRenderActor');loop=node('TFPHUD_NoteLoop')
 if not loop:loop=e.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop');loop.rename('TFPHUD_NoteLoop')
 w(prev,get.find_execute_pin());w(get.find_then_pin(),loop.find_input_pin('Exec'));w(get.find_output_pin('OutActors'),loop.find_input_pin('Array'));hide=fn('TFPHUD_HideWorldNotes','/Script/Engine.Actor:SetActorHiddenInGame');hide.find_input_pin('bNewHidden').set_pin_value('true');w(loop.find_output_pin('Array Element'),hide.find_self_pin());w(loop.find_output_pin('LoopBody'),hide.find_execute_pin())
 del e,event,cl,draw,ammo,cast,reserve,result,number,label,tail,begin,timer,cleanup,prev,get,loop,hide
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['status']=str(b.get_editor_property('status'));R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR
 if R['ok']:R['saved']=E.save_loaded_asset(b,False)
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_hud_layout.json'),'w'),indent=1)
