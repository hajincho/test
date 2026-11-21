"""헤드리스(세션당 한 번): 무기창 키/클릭 수정.
 1) OnKeyDown 의 키 비교(승격 연산자 Equal(Key)) B 값이 비어 있었음 -> 키 이름(Tab/Escape/One..Six) 직접 설정 후 읽어서 확인
 2) OnMouseButtonDown: TabRow 캐시 지오메트리가 Lyra UI 레이어에서 0 이라 위치 계산이 항상 실패 -> 누른 순간 마우스가 올라가 있는 Tab_i(IsHovered)로 전환
 -> Data/lyra_weapon_menu_fix3.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'keys': {}}
def run():
    wbp = unreal.load_asset(FULL)
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnKeyDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    for nm, key in [('WK_Tab', 'Tab'), ('WK_Esc', 'Escape')] + [('WK_K%d' % i, k) for i, k in enumerate(['One', 'Two', 'Three', 'Four', 'Five', 'Six'])]:
        b = pin(N[nm], 'B'); b.set_pin_value(key); R['keys'][nm] = str(b.get_pin_value())
    del ed, N
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
    others = [n for n in N.values() if n is not entry]
    for n in others:
        for p in n.list_all_pins(): p.break_pin_links()
    entry.find_then_pin().break_pin_links(); ed.remove_nodes(others); R['removed'] = len(others)
    def ret(nm, handled):
        r = ed.add_return_node(); h = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:' + ('Handled' if handled else 'Unhandled')); h.rename(nm)
        link(pin(h, 'ReturnValue', True), pin(r, 'ReturnValue')); return r
    prev = entry.find_then_pin()
    for i in range(6):
        g = ed.add_get_member_variable_node('Tab_%d' % i); g.rename('WH_Tab%d' % i)
        hv = ed.add_call_function_node('/Script/UMG.Widget:IsHovered'); assert hv; hv.rename('WH_Hov%d' % i); link(pin(g, 'Tab_%d' % i, True), hv.find_self_pin())
        br = ed.add_branch_node(); br.rename('WH_Br%d' % i); link(pin(hv, 'ReturnValue', True), pin(br, 'Condition')); link(prev, br.find_execute_pin())
        sv = ed.add_set_member_variable_node('NationIndex'); sv.rename('WH_Set%d' % i); pin(sv, 'NationIndex').set_pin_value(str(i))
        ap = ed.add_call_function_node(FULL + '.WBP_FurinaWeaponMenu_C:ApplyNation'); assert ap; ap.rename('WH_Apply%d' % i)
        link(br.find_then_pin(), sv.find_execute_pin()); link(sv.find_then_pin(), ap.find_execute_pin()); link(ap.find_then_pin(), ret('WH_Ret%d' % i, True).find_execute_pin())
        prev = br.find_else_pin()
    link(prev, ret('WH_RetNo', False).find_execute_pin())
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnKeyDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    R['keys_after_compile'] = {nm: str(pin(N[nm], 'B').get_pin_value()) for nm in R['keys']}
    del ed, N
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_fix3.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_FIX3', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
