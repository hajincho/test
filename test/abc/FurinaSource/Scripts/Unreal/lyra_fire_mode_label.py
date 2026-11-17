import unreal, json, traceback
OUT=r'L:\FurinaSource\Data\lyra_fire_mode_label.json'; R={}
PL=unreal.BlueprintGraphPinLibrary
def w(a,b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(),'pin'
    assert PL.try_create_connection(a,b),'link %s->%s'%(a.get_pin_name(),b.get_pin_name())
try:
    hb=unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); e=unreal.BlueprintGraphEditor.get_graph_editor_by_name(hb,'EventGraph')
    def node(n): return next((x for x in e.list_all_nodes() if x.get_name()==n),None)
    def fn(name,path):
        n=node(name)
        if not n:
            n=e.add_call_function_node(path); assert n,path; n.rename(name)
        return n
    draw=node('FM_DrawMode'); assert draw,'FM_DrawMode missing'
    # Y: 프레임 위쪽 바깥 (Y - 높이*0.17)
    node('FM_HudYOff').find_input_pin('B').set_pin_value('0.64')
    # X: 프레임 왼쪽 + 폭*0.03 (숫자 X 대신)
    xo=fn('FM_HudXOff','/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble'); w(node('TFPHUD_Width').find_result_pin(),xo.find_input_pin('A')); xo.find_input_pin('B').set_pin_value('0.545')
    xx=fn('FM_HudX','/Script/Engine.KismetMathLibrary:Add_DoubleDouble'); w(node('TFPHUD_X').find_result_pin(),xx.find_input_pin('A')); w(xo.find_result_pin(),xx.find_input_pin('B'))
    sx=draw.find_input_pin('ScreenX'); sx.break_pin_links(); w(xx.find_result_pin(),sx)
    unreal.BlueprintEditorLibrary.compile_blueprint(hb); R['status']=str(hb.get_editor_property('status'))
    if hb.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR: R['saved']=unreal.EditorAssetLibrary.save_loaded_asset(hb,False)
except Exception: R['error']=traceback.format_exc()
json.dump(R,open(OUT,'w',encoding='utf-8'),indent=1,ensure_ascii=False); print('FM_LABEL',R)


