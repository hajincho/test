import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 b=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD');e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,'EventGraph')
 def w(a,c):assert a.is_valid() and c.is_valid() and unreal.BlueprintGraphPinLibrary.try_create_connection(a,c)
 def fn(name,path):
  n=e.add_call_function_node(path);assert n,path;n.rename('TFPTest_'+name);return n
 ev=e.add_custom_event_node('FurinaTestRenderHUD');ev.rename('TFPTest_RenderHUD');self=e.create_node_from_name('Variables|셀프레퍼런스가져오기',unreal.Vector2D(0,0),[]);self.rename('TFPTest_Self');sp=self.find_output_pin('self')
 rt=fn('RT','/Script/Engine.KismetRenderingLibrary:CreateRenderTarget2D');rt.find_input_pin('Width').set_pin_value('1280');rt.find_input_pin('Height').set_pin_value('720');rt.find_input_pin('Format').set_pin_value('RTF_RGBA8');rt.find_input_pin('ClearColor').set_pin_value('(R=0.025,G=0.025,B=0.025,A=1)');w(ev.find_then_pin(),rt.find_execute_pin())
 begin=fn('Begin','/Script/Engine.KismetRenderingLibrary:BeginDrawCanvasToRenderTarget');w(rt.find_result_pin(),begin.find_input_pin('TextureRenderTarget'));w(rt.find_then_pin(),begin.find_execute_pin())
 set=fn('Canvas','/Script/Engine.KismetSystemLibrary:SetObjectPropertyByName');w(sp,set.find_input_pin('Object'));set.find_input_pin('PropertyName').set_pin_value('Canvas');w(begin.find_output_pin('Canvas'),set.find_input_pin('Value'));w(begin.find_then_pin(),set.find_execute_pin())
 finish=e.add_custom_event_node('FurinaTestFinishHUD');finish.rename('TFPTest_FinishHUD')
 end=fn('End','/Script/Engine.KismetRenderingLibrary:EndDrawCanvasToRenderTarget');w(begin.find_output_pin('Context'),end.find_input_pin('Context'));w(finish.find_then_pin(),end.find_execute_pin())
 export=fn('Export','/Script/Engine.KismetRenderingLibrary:ExportRenderTarget');w(rt.find_result_pin(),export.find_input_pin('TextureRenderTarget'));export.find_input_pin('FilePath').set_pin_value(r'C:\Users\fromj\Downloads\test\test\abc\Saved\Screenshots\WindowsEditor');export.find_input_pin('FileName').set_pin_value('TFP_HUD.png');w(end.find_then_pin(),export.find_execute_pin())
 clear=fn('CanvasRestore','/Script/Engine.KismetSystemLibrary:SetObjectPropertyByName');w(sp,clear.find_input_pin('Object'));clear.find_input_pin('PropertyName').set_pin_value('Canvas');w(export.find_then_pin(),clear.find_execute_pin())
 del e,ev,self,sp,rt,begin,set,finish,end,export,clear
 unreal.BlueprintEditorLibrary.compile_blueprint(b);R['ok']=b.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR;R['status']=str(b.get_editor_property('status'))
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_hud_fixture.json'),'w'),ensure_ascii=False,indent=1)
