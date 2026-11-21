"""헤드리스(세션당 한 번): 푸리나 폰 Tab -> 개발자용 무기 선택창 열기/닫기.
 기존 Tab 키 노드(K2Node_InputKey_1, 마우스 상하 반전 토글)의 Pressed 를 무기창으로 바꾼다(반전 토글 노드는 남기되 연결 해제).
 Tab / 커스텀 이벤트 FurinaWeaponMenuToggle ->
   위젯 변수 FurinaWeaponMenu 가 없으면 생성(WBP_FurinaWeaponMenu, 플레이어 0) ->
   화면에 있으면: 제거 + 게임 전용 입력 + 커서 숨김 / 없으면: 화면에 추가 + UI 전용 입력(위젯 포커스) + 커서 보임
 (열린 동안 입력은 UI 전용이라 Tab/Esc 닫기는 위젯의 OnKeyDown 이 처리)   노드: FWM_*   -> Data/lyra_weapon_menu_pawn.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN); wcls = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu').generated_class()
    if 'FurinaWeaponMenu' not in [str(x) for x in BEL.list_member_variable_names(bp)]:
        R['var'] = bool(BEL.add_member_variable(bp, 'FurinaWeaponMenu', BEL.get_object_reference_type(unreal.UserWidget)))
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
    if 'FWM_Br' in N: R['note'] = 'exists'; return bp
    tab = N['K2Node_InputKey_1']; pr = tab.find_output_pin('Pressed'); R['tab_old'] = [p.get_owning_node().get_name() for p in pr.list_connected_pins()]; pr.break_pin_links()
    ev = ed.add_custom_event_node('FurinaWeaponMenuToggle'); ev.rename('FWM_Event')
    iv = fn('FWM_IsValid', '/Script/Engine.KismetSystemLibrary:IsValid'); link(getw('FWM_W0'), pin(iv, 'Object'))
    br = ed.add_branch_node(); br.rename('FWM_Br'); link(pin(iv, 'ReturnValue', True), pin(br, 'Condition'))
    link(pr, br.find_execute_pin()); link(ev.find_then_pin(), br.find_execute_pin())
    pc = fn('FWM_PC', '/Script/Engine.GameplayStatics:GetPlayerController', PlayerIndex=0); PC = pin(pc, 'ReturnValue', True)
    cw = fn('FWM_Create', '/Script/UMG.WidgetBlueprintLibrary:Create'); pin(cw, 'WidgetType').set_pin_value(wcls.get_path_name()); link(PC, pin(cw, 'OwningPlayer'))
    sv = ed.add_set_member_variable_node('FurinaWeaponMenu'); sv.rename('FWM_Set'); link(pin(cw, 'ReturnValue', True), pin(sv, 'FurinaWeaponMenu'))
    link(br.find_else_pin(), cw.find_execute_pin()); link(cw.find_then_pin(), sv.find_execute_pin())
    inv = fn('FWM_InVP', '/Script/UMG.Widget:IsInViewport'); link(getw('FWM_W1'), inv.find_self_pin())
    b2 = ed.add_branch_node(); b2.rename('FWM_Br2'); link(pin(inv, 'ReturnValue', True), pin(b2, 'Condition'))
    link(br.find_then_pin(), b2.find_execute_pin()); link(sv.find_then_pin(), b2.find_execute_pin())
    # 닫기
    rm = fn('FWM_Remove', '/Script/UMG.Widget:RemoveFromParent'); link(getw('FWM_W2'), rm.find_self_pin())
    go = fn('FWM_GameOnly', '/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly'); link(PC, pin(go, 'PlayerController'))
    c0 = fn('FWM_CursorOff', '/Script/Engine.KismetSystemLibrary:SetBoolPropertyByName', PropertyName='bShowMouseCursor', Value='false'); link(PC, pin(c0, 'Object'))
    link(b2.find_then_pin(), rm.find_execute_pin()); link(rm.find_then_pin(), go.find_execute_pin()); link(go.find_then_pin(), c0.find_execute_pin())
    # 열기
    av = fn('FWM_AddVP', '/Script/UMG.UserWidget:AddToViewport', ZOrder=50); link(getw('FWM_W3'), av.find_self_pin())
    ui = fn('FWM_UIOnly', '/Script/UMG.WidgetBlueprintLibrary:SetInputMode_UIOnlyEx', InMouseLockMode='DoNotLock'); link(PC, pin(ui, 'PlayerController')); link(getw('FWM_W4'), pin(ui, 'InWidgetToFocus'))
    c1 = fn('FWM_CursorOn', '/Script/Engine.KismetSystemLibrary:SetBoolPropertyByName', PropertyName='bShowMouseCursor', Value='true'); link(PC, pin(c1, 'Object'))
    link(b2.find_else_pin(), av.find_execute_pin()); link(av.find_then_pin(), ui.find_execute_pin()); link(ui.find_then_pin(), c1.find_execute_pin())
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
json.dump(R, open(D + r'\lyra_weapon_menu_pawn.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_PAWN', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
