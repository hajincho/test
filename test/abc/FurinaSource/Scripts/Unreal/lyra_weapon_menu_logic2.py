"""헤드리스(세션당 한 번): WBP_FurinaWeaponMenu 국가 탭 전환 로직.
 - 변수 NationIndex(int), 커스텀 이벤트 ApplyNation: Nation_i 보이기/접기 + Tab_i 불투명도(선택 1.0 / 나머지 0.45)
 - OnKeyDown: Tab/Esc -> CloseMenu, 숫자 1~6 -> NationIndex 설정 + ApplyNation (Handled), 그 밖 Unhandled
 - OnMouseButtonDown: 클릭 위치가 TabRow 안이면 가로 위치로 탭 번호(0~5) 계산 -> 전환 (Handled), 아니면 Unhandled
 노드: WN_* / WK_* / WC_*   -> Data/lyra_weapon_menu_logic2.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
K = '/Script/Engine.KismetMathLibrary:'; KI = '/Script/Engine.KismetInputLibrary:'; UW = '/Script/UMG.UserWidget:'; WG = '/Script/UMG.Widget:'
KEYS = ['One', 'Two', 'Three', 'Four', 'Five', 'Six']
R = {'log': []}
def run():
    wbp = unreal.load_asset(FULL)
    if 'NationIndex' not in [str(x) for x in BEL.list_member_variable_names(wbp)]:
        R['var'] = bool(BEL.add_member_variable(wbp, 'NationIndex', BEL.get_basic_type_by_name('int')))
    wt = unreal.find_object(None, FULL + '.WBP_FurinaWeaponMenu:WidgetTree')
    VARS = ['TabRow'] + ['Nation_%d' % i for i in range(6)] + ['Tab_%d' % i for i in range(6)]
    for o in unreal.ObjectIterator(unreal.Widget):
        if o.get_outer() == wt and o.get_name() in VARS:
            unreal.get_default_object(unreal.SystemLibrary).call_method('SetBoolPropertyByName', (o, 'bIsVariable', True)); R.setdefault('vars_set', []).append(o.get_name())
    BEL.compile_blueprint(wbp)
    R['members'] = [str(x) for x in BEL.list_member_variable_names(wbp)]
    def tools(ed):
        def pin(n, name, out=False):
            p = n.find_output_pin(name) if out else n.find_input_pin(name)
            assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
        def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
        def fn(name, path, **vals):
            n = ed.add_call_function_node(path); assert n, path; n.rename(name)
            for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
            return n
        return pin, link, fn
    # 1) ApplyNation
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    pin, link, fn = tools(ed)
    if 'WN_Event' not in N:
        ev = ed.add_custom_event_node('ApplyNation'); ev.rename('WN_Event'); prevs = [ev.find_then_pin()]
        for i in range(6):
            g = ed.add_get_member_variable_node('NationIndex'); g.rename('WN_Get%d' % i)
            ir = fn('WN_Is%d' % i, K + 'InRange_IntInt', Min=i, Max=i, InclusiveMin='true', InclusiveMax='true'); link(pin(g, 'NationIndex', True), pin(ir, 'Value'))
            br = ed.add_branch_node(); br.rename('WN_Br%d' % i); link(pin(ir, 'ReturnValue', True), pin(br, 'Condition'))
            for pp in prevs: link(pp, br.find_execute_pin())
            outs = []
            for on, vis, op in (('On', 'Visible', 1.0), ('Off', 'Collapsed', 0.45)):
                gn = ed.add_get_member_variable_node('Nation_%d' % i); gn.rename('WN_Nat%s%d' % (on, i))
                sv = fn('WN_Vis%s%d' % (on, i), WG + 'SetVisibility', InVisibility=vis); link(pin(gn, 'Nation_%d' % i, True), sv.find_self_pin())
                gt = ed.add_get_member_variable_node('Tab_%d' % i); gt.rename('WN_Tab%s%d' % (on, i))
                so = fn('WN_Op%s%d' % (on, i), WG + 'SetRenderOpacity', InOpacity=op); link(pin(gt, 'Tab_%d' % i, True), so.find_self_pin())
                link(br.find_then_pin() if on == 'On' else br.find_else_pin(), sv.find_execute_pin()); link(sv.find_then_pin(), so.find_execute_pin()); outs.append(so.find_then_pin())
            prevs = outs
        R['log'].append('apply')
    del ed, N
    BEL.compile_blueprint(wbp)
    # 2) OnKeyDown 다시 짜기
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnKeyDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    pin, link, fn = tools(ed)
    if 'WK_Br0' not in N:
        entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
        others = [n for n in N.values() if n is not entry]
        for n in others:
            for p in n.list_all_pins(): p.break_pin_links()
        try: ed.remove_nodes(others); R['log'].append('removed %d' % len(others))
        except Exception as e: R['remove_err'] = str(e)[:150]
        gk = fn('WK_GetKey', KI + 'GetKey'); link(pin(entry, 'InKeyEvent', True), pin(gk, 'Input')); KEY = pin(gk, 'ReturnValue', True)
        def isk(nm, keyname):
            e = fn(nm, KI + 'EqualEqual_KeyKey'); link(KEY, pin(e, 'A')); pin(e, 'B').set_pin_value('(KeyName="%s")' % keyname); return pin(e, 'ReturnValue', True)
        def ret(nm, handled):
            r = ed.add_return_node(); h = fn(nm + 'V', '/Script/UMG.WidgetBlueprintLibrary:' + ('Handled' if handled else 'Unhandled')); link(pin(h, 'ReturnValue', True), pin(r, 'ReturnValue')); return r
        orn = fn('WK_Or', K + 'BooleanOR'); link(isk('WK_Tab', 'Tab'), pin(orn, 'A')); link(isk('WK_Esc', 'Escape'), pin(orn, 'B'))
        bc = ed.add_branch_node(); bc.rename('WK_BrClose'); link(pin(orn, 'ReturnValue', True), pin(bc, 'Condition')); link(entry.find_then_pin(), bc.find_execute_pin())
        cl = ed.add_call_function_node(FULL + '.WBP_FurinaWeaponMenu_C:CloseMenu'); assert cl; cl.rename('WK_Close')
        link(bc.find_then_pin(), cl.find_execute_pin()); link(cl.find_then_pin(), ret('WK_RetClose', True).find_execute_pin())
        prev = bc.find_else_pin()
        for i, kn in enumerate(KEYS):
            b = ed.add_branch_node(); b.rename('WK_Br%d' % i); link(isk('WK_K%d' % i, kn), pin(b, 'Condition')); link(prev, b.find_execute_pin())
            sv = ed.add_set_member_variable_node('NationIndex'); sv.rename('WK_Set%d' % i); pin(sv, 'NationIndex').set_pin_value(str(i))
            ap = ed.add_call_function_node(FULL + '.WBP_FurinaWeaponMenu_C:ApplyNation'); assert ap; ap.rename('WK_Apply%d' % i)
            link(b.find_then_pin(), sv.find_execute_pin()); link(sv.find_then_pin(), ap.find_execute_pin()); link(ap.find_then_pin(), ret('WK_Ret%d' % i, True).find_execute_pin())
            prev = b.find_else_pin()
        link(prev, ret('WK_RetNo', False).find_execute_pin())
        R['log'].append('keydown')
    del ed, N
    # 3) OnMouseButtonDown: 탭 클릭
    if 'OnMouseButtonDown' not in [str(g) for g in BEL.list_graph_names(wbp)]:
        BEL.add_function_override(wbp, 'OnMouseButtonDown')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    pin, link, fn = tools(ed)
    if 'WC_Br' not in N:
        entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
        res = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionResult']
        for n in N.values():
            if n is not entry and n not in res:
                for p in n.list_all_pins(): p.break_pin_links()
        entry.find_then_pin().break_pin_links()
        R['mbd_entry_pins'] = [str(p.get_pin_name()) for p in entry.list_all_pins()]
        tr = ed.add_get_member_variable_node('TabRow'); tr.rename('WC_TabRow')
        geo = fn('WC_Geo', WG + 'GetCachedGeometry'); link(pin(tr, 'TabRow', True), geo.find_self_pin())
        sp = fn('WC_ScreenPos', KI + 'PointerEvent_GetScreenSpacePosition'); link(pin(entry, 'MouseEvent', True), pin(sp, 'Input'))
        loc = fn('WC_Local', '/Script/UMG.SlateBlueprintLibrary:AbsoluteToLocal'); link(pin(geo, 'ReturnValue', True), pin(loc, 'Geometry')); link(pin(sp, 'ReturnValue', True), pin(loc, 'AbsoluteCoordinate'))
        sz = fn('WC_Size', '/Script/UMG.SlateBlueprintLibrary:GetLocalSize'); link(pin(geo, 'ReturnValue', True), pin(sz, 'Geometry'))
        bl = fn('WC_BrkLoc', K + 'BreakVector2D'); link(pin(loc, 'ReturnValue', True), pin(bl, 'InVec'))
        bs = fn('WC_BrkSize', K + 'BreakVector2D'); link(pin(sz, 'ReturnValue', True), pin(bs, 'InVec'))
        ix = fn('WC_InX', K + 'InRange_FloatFloat', Min=0.0, InclusiveMin='true', InclusiveMax='false'); link(pin(bl, 'X', True), pin(ix, 'Value')); link(pin(bs, 'X', True), pin(ix, 'Max'))
        iy = fn('WC_InY', K + 'InRange_FloatFloat', Min=0.0, InclusiveMin='true', InclusiveMax='true'); link(pin(bl, 'Y', True), pin(iy, 'Value')); link(pin(bs, 'Y', True), pin(iy, 'Max'))
        an = fn('WC_And', K + 'BooleanAND'); link(pin(ix, 'ReturnValue', True), pin(an, 'A')); link(pin(iy, 'ReturnValue', True), pin(an, 'B'))
        br = ed.add_branch_node(); br.rename('WC_Br'); link(pin(an, 'ReturnValue', True), pin(br, 'Condition')); link(entry.find_then_pin(), br.find_execute_pin())
        mr = fn('WC_Map', K + 'MapRangeClamped', InRangeA=0.0, OutRangeA=0.0, OutRangeB=5.999); link(pin(bl, 'X', True), pin(mr, 'Value')); link(pin(bs, 'X', True), pin(mr, 'InRangeB'))
        fl = fn('WC_Floor', K + 'FFloor'); link(pin(mr, 'ReturnValue', True), pin(fl, 'A'))
        sv = ed.add_set_member_variable_node('NationIndex'); sv.rename('WC_Set'); link(pin(fl, 'ReturnValue', True), pin(sv, 'NationIndex'))
        ap = ed.add_call_function_node(FULL + '.WBP_FurinaWeaponMenu_C:ApplyNation'); assert ap; ap.rename('WC_Apply')
        link(br.find_then_pin(), sv.find_execute_pin()); link(sv.find_then_pin(), ap.find_execute_pin())
        r1 = res[0] if res else ed.add_return_node(); r2 = ed.add_return_node()
        h = fn('WC_H', '/Script/UMG.WidgetBlueprintLibrary:Handled'); u = fn('WC_U', '/Script/UMG.WidgetBlueprintLibrary:Unhandled')
        link(ap.find_then_pin(), r1.find_execute_pin()); link(pin(h, 'ReturnValue', True), pin(r1, 'ReturnValue'))
        link(br.find_else_pin(), r2.find_execute_pin()); link(pin(u, 'ReturnValue', True), pin(r2, 'ReturnValue'))
        R['log'].append('mousedown')
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_logic2.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM_LOGIC2', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
