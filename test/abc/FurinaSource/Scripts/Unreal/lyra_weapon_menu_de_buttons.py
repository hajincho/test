"""헤드리스(세션당 한 번): 무기창 제3제국 탭 버튼 21개 활성 + 클릭 시 선택 기록(모션/장착 없음).
 - Btn_0_<병과>_<순위> 활성, 툴팁에 연결된 모델(키) 표시. 변수 지정: 버튼 21개 + 'Current' 글자
 - 변수 SelectedPrimary(문자열, 무기 이름), SelectedPrimaryKey(문자열, 모델 키, 조준경 합본은 kar98k_zf39 처럼 에셋 키와 같음)
 - OnPreviewMouseButtonDown 재정의: 마우스가 올라간 버튼이면 두 변수 설정 + 캐릭터(소유 폰)의 FurinaPrimaryKey 문자열에도 키 전달 + Current 글자 갱신 -> Unhandled
 -> Data/lyra_weapon_menu_de_buttons.json"""
import unreal, json, traceback, time
TOK = '%x' % (int(time.time()) % 0xFFFFF)   # 다시 실행할 때 지운 노드와 이름이 겹치지 않게(겹치면 엔진이 죽음)
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'; BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
CLASSES = ['장교', '보병', '돌격병', '대전차병', '중화기병', '저격수', '기갑병']
DE = [[('Walther P38', 'p38'), ('Luger P08', 'p08'), ('Walther PP', 'pp')], [('Kar98k', 'kar98k'), ('Gewehr 43', 'g43'), ('StG44', 'stg44')], [('MP40', 'mp40'), ('MP38', 'mp38'), ('StG44', 'stg44')],
      [('Panzerfaust', 'panzerfaust'), ('Panzerschreck', 'panzerschreck'), ('PzB 39', 'pzb39')], [('MG42', 'mg42'), ('MG34', 'mg34'), ('8cm GrW 34', 'grw34')],
      [('Kar98k (ZF39)', 'kar98k_zf39'), ('Kar98k (ZF41)', 'kar98k_zf41'), ('G43 (ZF4)', 'g43_zf4')], [('Walther P38', 'p38'), ('Luger P08', 'p08'), ('MP40', 'mp40')]]
R = {'log': []}
def run():
    wbp = unreal.load_asset(FULL); wt = unreal.find_object(None, FULL + '.WBP_FurinaWeaponMenu:WidgetTree')
    W = {o.get_name(): o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt and not o.get_name().startswith('Old')}
    sysl = unreal.get_default_object(unreal.SystemLibrary)
    for c in range(7):
        for k in range(3):
            b = W['Btn_0_%d_%d' % (c, k)]; nm, key = DE[c][k]
            b.set_is_enabled(True); b.set_tool_tip_text(unreal.Text('제3제국 / %s / %d순위: %s  (모델: %s, 모션 없음)' % (CLASSES[c], k + 1, nm, key)))
            sysl.call_method('SetBoolPropertyByName', (b, 'bIsVariable', True))
    sysl.call_method('SetBoolPropertyByName', (W['Current'], 'bIsVariable', True))
    names = [str(x) for x in BEL.list_member_variable_names(wbp)]
    for v in ('SelectedPrimary', 'SelectedPrimaryKey'):
        if v not in names: BEL.add_member_variable(wbp, v, BEL.get_basic_type_by_name('string'))
    BEL.compile_blueprint(wbp)
    if 'OnPreviewMouseButtonDown' not in [str(g) for g in BEL.list_graph_names(wbp)]: BEL.add_function_override(wbp, 'OnPreviewMouseButtonDown')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnPreviewMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
    others = [n for n in N.values() if n is not entry]
    for n in others:
        for p in n.list_all_pins(): p.break_pin_links()
    entry.find_then_pin().break_pin_links()
    if others: ed.remove_nodes(others)
    def ret(nm):
        r = ed.add_return_node(); u = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:Unhandled'); u.rename(nm + '_U'); link(pin(u, 'ReturnValue', True), pin(r, 'ReturnValue')); return r
    prev = entry.find_then_pin(); R['text_vals'] = []
    for c in range(7):
        for k in range(3):
            bn = 'Btn_0_%d_%d' % (c, k); nm, key = DE[c][k]
            g = ed.add_get_member_variable_node(bn); g.rename('WS_G_%d_%d_%s' % (c, k, TOK))
            hv = ed.add_call_function_node('/Script/UMG.Widget:IsHovered'); hv.rename('WS_H_%d_%d_%s' % (c, k, TOK)); link(pin(g, bn, True), hv.find_self_pin())
            br = ed.add_branch_node(); br.rename('WS_B_%d_%d_%s' % (c, k, TOK)); link(pin(hv, 'ReturnValue', True), pin(br, 'Condition')); link(prev, br.find_execute_pin())
            s1 = ed.add_set_member_variable_node('SelectedPrimary'); s1.rename('WS_S1_%d_%d_%s' % (c, k, TOK)); pin(s1, 'SelectedPrimary').set_pin_value(nm)
            s2 = ed.add_set_member_variable_node('SelectedPrimaryKey'); s2.rename('WS_S2_%d_%d_%s' % (c, k, TOK)); pin(s2, 'SelectedPrimaryKey').set_pin_value(key)
            gc_ = ed.add_get_member_variable_node('Current'); gc_.rename('WS_C_%d_%d_%s' % (c, k, TOK))
            st = ed.add_call_function_node('/Script/UMG.TextBlock:SetText'); st.rename('WS_T_%d_%d_%s' % (c, k, TOK)); link(pin(gc_, 'Current', True), st.find_self_pin())
            txt = '현재 선택  1번: %s (제3제국 %s)   /   2번: 없음' % (nm, CLASSES[c]); pin(st, 'InText').set_pin_value(txt)
            if c == 0 and k == 0: R['text_vals'].append(str(pin(st, 'InText').get_pin_value()))
            op = ed.add_call_function_node('/Script/UMG.UserWidget:GetOwningPlayerPawn'); op.rename('WS_P_%d_%d_%s' % (c, k, TOK))
            sp = ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:SetStringPropertyByName'); sp.rename('WS_K_%d_%d_%s' % (c, k, TOK))
            link(pin(op, 'ReturnValue', True), pin(sp, 'Object')); pin(sp, 'PropertyName').set_pin_value('FurinaPrimaryKey'); pin(sp, 'Value').set_pin_value(key)
            link(br.find_then_pin(), s1.find_execute_pin()); link(s1.find_then_pin(), s2.find_execute_pin()); link(s2.find_then_pin(), sp.find_execute_pin()); link(sp.find_then_pin(), st.find_execute_pin())
            link(st.find_then_pin(), ret('WS_R_%d_%d_%s' % (c, k, TOK)).find_execute_pin())
            prev = br.find_else_pin()
    link(prev, ret('WS_RNo_' + TOK).find_execute_pin())
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    R['enabled'] = sum(1 for c in range(7) for k in range(3) if W['Btn_0_%d_%d' % (c, k)].get_is_enabled())
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_weapon_menu_de_buttons.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str); print('WM_DE_BTN', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
