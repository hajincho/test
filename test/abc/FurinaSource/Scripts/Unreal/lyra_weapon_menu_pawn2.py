"""헤드리스(세션당 한 번): 폰의 무기창 열기를 Lyra CommonUI 레이어 방식으로 교체.
 Tab(K2Node_InputKey_1) / FurinaWeaponMenuToggle ->
   변수 FurinaWeaponMenu(CommonActivatableWidget) 가 유효하고 활성 -> DeactivateWidget(닫기)
   아니면 -> PushContentToLayer_ForPlayer(로컬 플레이어, UI.Layer.GameMenu, WBP_FurinaWeaponMenu) -> 변수에 저장
 (열린 동안 CommonUI Menu 입력이라 게임 Tab 은 안 들어오고, 닫기는 위젯 OnKeyDown 의 Tab/Esc 가 처리)
 이전 FWM_* 노드(AddToViewport/SetInputMode 방식)는 지운다.   -> Data/lyra_weapon_menu_pawn2.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN); wcls = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu').generated_class()
    BEL.change_member_variable_type(bp, 'FurinaWeaponMenu', BEL.get_object_reference_type(unreal.CommonActivatableWidget))
    BEL.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    def fn(name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    def getw(name): n = ed.add_get_member_variable_node('FurinaWeaponMenu'); n.rename(name); return pin(n, 'FurinaWeaponMenu', True)
    if 'FWM2_Push' in N: R['note'] = 'exists'; return bp
    old = [n for k, n in N.items() if k.startswith('FWM_') and k != 'FWM_Event']
    for n in old:
        for p in n.list_all_pins(): p.break_pin_links()
    ed.remove_nodes(old); R['removed'] = len(old)
    ev = N['FWM_Event']; tab = N['K2Node_InputKey_1']; pr = tab.find_output_pin('Pressed'); pr.break_pin_links(); ev.find_then_pin().break_pin_links()
    iv = fn('FWM2_IsValid', '/Script/Engine.KismetSystemLibrary:IsValid'); link(getw('FWM2_W0'), pin(iv, 'Object'))
    br = ed.add_branch_node(); br.rename('FWM2_Br'); link(pin(iv, 'ReturnValue', True), pin(br, 'Condition'))
    link(pr, br.find_execute_pin()); link(ev.find_then_pin(), br.find_execute_pin())
    ia = fn('FWM2_IsAct', '/Script/CommonUI.CommonActivatableWidget:IsActivated'); link(getw('FWM2_W1'), ia.find_self_pin())
    b2 = ed.add_branch_node(); b2.rename('FWM2_Br2'); link(pin(ia, 'ReturnValue', True), pin(b2, 'Condition')); link(br.find_then_pin(), b2.find_execute_pin())
    dw = fn('FWM2_Close', '/Script/CommonUI.CommonActivatableWidget:DeactivateWidget'); link(getw('FWM2_W2'), dw.find_self_pin()); link(b2.find_then_pin(), dw.find_execute_pin())
    pc = fn('FWM2_PC', '/Script/Engine.GameplayStatics:GetPlayerController', PlayerIndex=0)
    lp = fn('FWM2_LP', '/Script/CommonGame.CommonUIExtensions:GetLocalPlayerFromController'); link(pin(pc, 'ReturnValue', True), pin(lp, 'PlayerController'))
    pu = fn('FWM2_Push', '/Script/CommonGame.CommonUIExtensions:PushContentToLayer_ForPlayer'); link(pin(lp, 'ReturnValue', True), pin(pu, 'LocalPlayer'))
    pin(pu, 'LayerName').set_pin_value('(TagName="UI.Layer.GameMenu")'); pin(pu, 'WidgetClass').set_pin_value(wcls.get_path_name())
    R['push_pins'] = [str(pin(pu, 'LayerName').get_pin_value()), str(pin(pu, 'WidgetClass').get_pin_value())]
    sv = ed.add_set_member_variable_node('FurinaWeaponMenu'); sv.rename('FWM2_Set'); link(pin(pu, 'ReturnValue', True), pin(sv, 'FurinaWeaponMenu'))
    link(br.find_else_pin(), lp.find_execute_pin()); link(b2.find_else_pin(), lp.find_execute_pin())
    link(lp.find_then_pin(), pu.find_execute_pin()); link(pu.find_then_pin(), sv.find_execute_pin())
    R['added'] = True
    del ed, N
    import gc; gc.collect()
    return bp
try:
    bp = run()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_pawn2.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_PAWN2', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
