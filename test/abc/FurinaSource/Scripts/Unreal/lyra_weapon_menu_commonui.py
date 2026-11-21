"""헤드리스(세션당 한 번): WBP_FurinaWeaponMenu 를 Lyra CommonUI 방식으로.
 - 부모 UserWidget -> LyraActivatableWidget, InputConfig = Menu(커서 보임, 게임 입력 차단), 뒤로 가기(Esc) 처리, 포커스 가능
 - BP_GetDesiredFocusTarget 재정의: 자기 자신(GetOuterUserWidget(TabRow)) -> 키 입력이 위젯 OnKeyDown 으로 들어옴
 - CloseMenu: DeactivateWidget (CommonUI 가 입력 모드 복원, 레이어 스택에서 제거)   -> Data/lyra_weapon_menu_commonui.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    wbp = unreal.load_asset(FULL)
    parent = unreal.load_class(None, '/Script/LyraGame.LyraActivatableWidget'); R['parent'] = str(parent)
    BEL.reparent_blueprint(wbp, parent); BEL.compile_blueprint(wbp)
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    # CloseMenu -> DeactivateWidget
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    old = [N[k] for k in ('WM_Remove', 'WM_OwnPC', 'WM_GameOnly', 'WM_Cursor') if k in N]
    for n in old:
        for p in n.list_all_pins(): p.break_pin_links()
    if old: ed.remove_nodes(old); R['log'].append('removed old close nodes %d' % len(old))
    ev = N['WM_Close']; ev.find_then_pin().break_pin_links()
    dw = ed.add_call_function_node('/Script/CommonUI.CommonActivatableWidget:DeactivateWidget'); assert dw; dw.rename('WM_Deactivate')
    link(ev.find_then_pin(), dw.find_execute_pin())
    del ed, N
    # 포커스 대상 = 자기 자신
    if 'BP_GetDesiredFocusTarget' not in [str(g) for g in BEL.list_graph_names(wbp)]:
        BEL.add_function_override(wbp, 'BP_GetDesiredFocusTarget')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'BP_GetDesiredFocusTarget'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
    res = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionResult']
    r = res[0] if res else ed.add_return_node()
    if not list(entry.find_then_pin().list_connected_pins()): link(entry.find_then_pin(), r.find_execute_pin())
    tr = ed.add_get_member_variable_node('TabRow'); tr.rename('WF_TabRow')
    ow = ed.add_call_function_node('/Script/UMG.UserWidgetFunctionLibrary:GetOuterUserWidget'); assert ow; ow.rename('WF_Self')
    link(pin(tr, 'TabRow', True), pin(ow, 'Widget')); link(pin(ow, 'ReturnValue', True), pin(r, 'ReturnValue'))
    R['log'].append('focus target')
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(wbp)
    cdo = unreal.get_default_object(wbp.generated_class())
    for pn, v in (('input_config', unreal.LyraWidgetInputMode.MENU), ('is_back_handler', True), ('is_focusable', True)):
        try: cdo.set_editor_property(pn, v); R['log'].append('cdo %s' % pn)
        except Exception as e: R.setdefault('cdo_err', []).append([pn, str(e)[:120]])
    BEL.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    c2 = unreal.get_default_object(wbp.generated_class()); R['check'] = {pn: str(c2.get_editor_property(pn)) for pn in ('input_config', 'is_back_handler', 'is_focusable')}
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_commonui.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_CUI', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
