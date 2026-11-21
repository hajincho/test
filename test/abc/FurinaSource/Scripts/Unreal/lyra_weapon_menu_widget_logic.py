"""헤드리스(세션당 한 번): WBP_FurinaWeaponMenu 닫기 로직.
 - 커스텀 이벤트 CloseMenu: RemoveFromParent -> 입력 모드 게임 전용 -> 마우스 커서 숨김
 - OnKeyDown 재정의: Tab 또는 Esc 면 CloseMenu 호출 후 Handled, 아니면 Unhandled
 - 위젯 포커스 가능(bIsFocusable)   노드: WM_*   -> Data/lyra_weapon_menu_widget_logic.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    wbp = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu')
    R['bel'] = [m for m in dir(BEL) if 'type' in m.lower()]
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    def fn(ed, name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    # 1) 이벤트 그래프: CloseMenu
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'WM_Close' not in N:
        ev = ed.add_custom_event_node('CloseMenu'); ev.rename('WM_Close')
        rm = fn(ed, 'WM_Remove', '/Script/UMG.Widget:RemoveFromParent')
        op = fn(ed, 'WM_OwnPC', '/Script/Engine.GameplayStatics:GetPlayerController', PlayerIndex=0)
        gm = fn(ed, 'WM_GameOnly', '/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly'); link(pin(op, 'ReturnValue', True), pin(gm, 'PlayerController'))
        cur = fn(ed, 'WM_Cursor', '/Script/Engine.KismetSystemLibrary:SetBoolPropertyByName', PropertyName='bShowMouseCursor', Value='false'); link(pin(op, 'ReturnValue', True), pin(cur, 'Object'))
        link(ev.find_then_pin(), rm.find_execute_pin()); link(rm.find_then_pin(), gm.find_execute_pin()); link(gm.find_then_pin(), cur.find_execute_pin())
        R['log'].append('close event')
    del ed, N
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    # 2) OnKeyDown 재정의
    names = [str(g) for g in BEL.list_graph_names(wbp)] if hasattr(BEL, 'list_graph_names') else []
    if 'OnKeyDown' not in names:
        g = BEL.add_function_override(wbp, 'OnKeyDown'); R['override'] = str(g)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnKeyDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    R['okd_nodes'] = {k: n.get_class().get_name() for k, n in N.items()}
    if 'WM_KeyBr' not in N:
        entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
        res = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionResult']
        # 기존 연결(부모 호출 등) 제거
        for n in N.values():
            if n not in [entry] + res:
                for p in n.list_all_pins(): p.break_pin_links()
        entry.find_then_pin().break_pin_links()
        gk = fn(ed, 'WM_GetKey', '/Script/Engine.KismetInputLibrary:GetKey'); link(pin(entry, 'InKeyEvent', True), pin(gk, 'Input'))
        eqT = fn(ed, 'WM_IsTab', '/Script/Engine.KismetInputLibrary:EqualEqual_KeyKey'); link(pin(gk, 'ReturnValue', True), pin(eqT, 'A')); pin(eqT, 'B').set_pin_value('(KeyName="Tab")')
        eqE = fn(ed, 'WM_IsEsc', '/Script/Engine.KismetInputLibrary:EqualEqual_KeyKey'); link(pin(gk, 'ReturnValue', True), pin(eqE, 'A')); pin(eqE, 'B').set_pin_value('(KeyName="Escape")')
        R['keyB'] = [str(pin(eqT, 'B').get_pin_value()), str(pin(eqE, 'B').get_pin_value())]
        orn = fn(ed, 'WM_Or', '/Script/Engine.KismetMathLibrary:BooleanOR'); link(pin(eqT, 'ReturnValue', True), pin(orn, 'A')); link(pin(eqE, 'ReturnValue', True), pin(orn, 'B'))
        br = ed.add_branch_node(); br.rename('WM_KeyBr'); link(pin(orn, 'ReturnValue', True), pin(br, 'Condition'))
        link(entry.find_then_pin(), br.find_execute_pin())
        cl = ed.add_call_function_node('/Game/Furina/UI/WBP_FurinaWeaponMenu.WBP_FurinaWeaponMenu_C:CloseMenu'); assert cl, 'CloseMenu call'; cl.rename('WM_CallClose')
        link(br.find_then_pin(), cl.find_execute_pin())
        r1 = res[0] if res else ed.add_return_node(); r2 = ed.add_return_node()
        h = fn(ed, 'WM_Handled', '/Script/UMG.WidgetBlueprintLibrary:Handled'); u = fn(ed, 'WM_Unhandled', '/Script/UMG.WidgetBlueprintLibrary:Unhandled')
        link(cl.find_then_pin(), r1.find_execute_pin()); link(pin(h, 'ReturnValue', True), pin(r1, 'ReturnValue'))
        link(br.find_else_pin(), r2.find_execute_pin()); link(pin(u, 'ReturnValue', True), pin(r2, 'ReturnValue'))
        R['log'].append('onkeydown')
    del ed, N
    import gc; gc.collect()
    cdo = unreal.get_default_object(wbp.generated_class())
    for pn in ('is_focusable', 'b_is_focusable'):
        try: cdo.set_editor_property(pn, True); R['focusable'] = pn; break
        except Exception as e: R.setdefault('focus_err', []).append(str(e)[:100])
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    try: R['focusable_after'] = bool(unreal.get_default_object(wbp.generated_class()).get_editor_property(R.get('focusable', 'is_focusable')))
    except Exception as e: R['focusable_after'] = str(e)[:80]
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_widget_logic.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_LOGIC', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
