"""헤드리스: WBP_FurinaWeaponMenu 를 '국가별 탭' 구성으로 다시 짠다(자산은 그대로 두고 루트 CanvasPanel 내용만 교체 -> 폰 참조 유지).
 국가 순서: 제3제국, 대일본제국, 이탈리아제국, 미국, 소비에트연방, 영국. 각 국가 = 병과 7행 x 1~3순위 버튼(모두 1번 주무기). 별표(★)는 뺌.
 위젯 이름: 탭 줄 TabRow, 탭 Tab_<국가>/TabTxt_<국가>, 국가 표 Nation_<국가>(GridPanel), 버튼 Btn_<국가>_<병과>_<순위>(0부터), 글자 Txt_<...>.
 처음엔 Nation_0 만 보임, 나머지 접힘. 무기가 아직 없어서 버튼은 전부 비활성.  -> Data/lyra_weapon_menu_widget2.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
CLASSES = ['장교', '보병', '돌격병', '대전차병', '중화기병', '저격수', '기갑병']
NATIONS = ['제3제국', '대일본제국', '이탈리아제국', '미국', '소비에트연방', '영국']
W = {
 '제3제국': [['Walther P38', 'Luger P08', 'Walther PP'], ['Kar98k', 'Gewehr 43', 'StG44'], ['MP40', 'MP38', 'StG44'], ['Panzerfaust', 'Panzerschreck', 'PzB 39'],
           ['MG42', 'MG34', '8cm GrW 34'], ['Kar98k (ZF39)', 'Kar98k (ZF41)', 'G43 (ZF4)'], ['Walther P38', 'Luger P08', 'MP40']],
 '대일본제국': [['14식 남부 권총', '94식 남부 권총', '26식 권총'], ['38식 소총', '99식 소총', '38식 기병총'], ['38식 소총', '99식 소총', '100식 기관단총'],
            ['94식 37mm 대전차포', '1식 47mm 대전차포', '97식 20mm 대전차총'], ['96식 경기관총', '99식 경기관총', '92식 중기관총'],
            ['97식 저격총', '99식 저격총', '38식 소총(조준사수)'], ['14식 남부 권총', '94식 남부 권총', '38식 기병총']],
 '이탈리아제국': [['Beretta M1934', 'Beretta M1935', 'Bodeo M1889'], ['Carcano M91', 'Carcano M91/38', 'Carcano M91/41'], ['Beretta M38A', 'Carcano M91/38 TS', 'Beretta M38/42'],
             ['Cannone 47/32', 'Breda 20/65 M35', 'Solothurn S-18/1000'], ['Breda M30', 'Breda M37', 'Fiat-Revelli M1914/35'],
             ['Carcano M91', 'Carcano M91/41', 'Carcano M91/38'], ['Beretta M1934', 'Beretta M1935', 'Bodeo M1889']],
 '미국': [['M1911A1', 'M1 Carbine', 'Thompson M1A1'], ['M1 Garand', 'M1903 Springfield', 'M1 Carbine'], ['Thompson M1A1', 'M3 Grease Gun', 'M1 Carbine'],
        ['M1A1 Bazooka', 'M9 Bazooka', '57mm Gun M1'], ['M1918A2 BAR', 'M1919A4', 'M2 Browning'], ['M1903A4 Springfield', 'M1903A1 Unertl', 'M1C Garand'],
        ['M1911A1', 'M3 Grease Gun', 'M1 Carbine']],
 '소비에트연방': [['TT-33', 'Nagant M1895', 'PPSh-41'], ['Mosin-Nagant M91/30', 'Mosin-Nagant M44', 'SVT-40'], ['PPSh-41', 'PPS-43', 'SVT-40'],
             ['PTRD-41', 'PTRS-41', '45mm 53-K 대전차포'], ['DP-27', 'Maxim M1910/30', 'SG-43'], ['Mosin M91/30 (PU)', 'Mosin M91/30 (PE/PEM)', 'SVT-40 (PU)'],
             ['TT-33', 'Nagant M1895', 'PPSh-41']],
 '영국': [['Enfield No.2 Mk I', 'Webley Mk IV', 'Webley Mk VI'], ['Lee-Enfield No.4 Mk I', 'SMLE No.1 Mk III*', 'Lee-Enfield No.5 Mk I'], ['Sten Mk II', 'Thompson M1928A1', 'Sten Mk V'],
        ['PIAT', 'Boys Anti-Tank Rifle', 'QF 6-pounder'], ['Bren Mk I/II', 'Vickers Mk I', '3-inch Mortar'],
        ['Lee-Enfield No.4 Mk I(T)', 'Pattern 1914 (T)', 'SMLE No.1 Mk III(조준경형)'], ['Enfield No.2 Mk I', 'Sten Mk II', 'Thompson M1928A1']],
}
R = {'log': []}
def run():
    wbp = unreal.load_asset(FULL)
    wt = unreal.find_object(None, FULL + '.WBP_FurinaWeaponMenu:WidgetTree')
    allw = [o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt]
    root = [o for o in allw if isinstance(o, unreal.CanvasPanel) and o.get_parent() is None][0]
    root.clear_children()
    for o in allw:   # 이전 위젯 이름 비우기(새 이름과 충돌 방지)
        if o != root and not o.get_name().startswith('Old'):
            o.rename('Old%d_%s' % (len(R['log']), o.get_name())); R['log'].append(o.get_name())
    def mk(cls, nm): return unreal.new_object(cls, outer=wt, name=nm)
    def txt(nm, s, size, bold=False, col=None):
        t = mk(unreal.TextBlock, nm); t.set_text(unreal.Text(s)); f = t.get_editor_property('font'); f.set_editor_property('size', size)
        if bold: f.set_editor_property('typeface_font_name', 'Bold')
        t.set_editor_property('font', f)
        if col: t.set_color_and_opacity(unreal.SlateColor(col))
        return t
    bd = mk(unreal.Border, 'Panel'); bd.set_editor_property('brush_color', unreal.LinearColor(0.02, 0.02, 0.03, 0.9)); bd.set_editor_property('padding', unreal.Margin(24, 20, 24, 20))
    cs = root.add_child_to_canvas(bd); cs.set_anchors(unreal.Anchors(unreal.Vector2D(0.5, 0.5), unreal.Vector2D(0.5, 0.5))); cs.set_alignment(unreal.Vector2D(0.5, 0.5)); cs.set_auto_size(True); cs.set_position(unreal.Vector2D(0, 0))
    vb = mk(unreal.VerticalBox, 'VBox'); bd.add_child(vb)
    def vadd(w, top=0, bottom=6): s = vb.add_child_to_vertical_box(w); s.set_padding(unreal.Margin(0, top, 0, bottom)); return s
    vadd(txt('Title', '무기 선택 (개발자용)', 26, True))
    vadd(txt('Help', '국가 전환: 탭 클릭 또는 숫자 1~6     닫기: Tab / Esc     회색 버튼 = 아직 추가되지 않은 무기', 15, False, unreal.LinearColor(0.75, 0.75, 0.75, 1)), 0, 12)
    tr = mk(unreal.HorizontalBox, 'TabRow'); vadd(tr, 0, 10)
    for i, nn in enumerate(NATIONS):
        sb = mk(unreal.SizeBox, 'TabBox_%d' % i); sb.set_width_override(190); sb.set_height_override(46)
        tb = mk(unreal.Border, 'Tab_%d' % i); tb.set_editor_property('brush_color', unreal.LinearColor(0.16, 0.22, 0.34, 1)); tb.set_editor_property('padding', unreal.Margin(4, 4, 4, 4))
        tb.set_editor_property('horizontal_alignment', unreal.HorizontalAlignment.H_ALIGN_CENTER); tb.set_editor_property('vertical_alignment', unreal.VerticalAlignment.V_ALIGN_CENTER)
        tb.add_child(txt('TabTxt_%d' % i, '%d  %s' % (i + 1, nn), 19, True)); sb.add_child(tb)
        tb.set_render_opacity(1.0 if i == 0 else 0.45)
        s = tr.add_child_to_horizontal_box(sb); s.set_padding(unreal.Margin(0, 0, 6, 0))
    vadd(txt('Slot1Head', '1번 무기 (주무기)', 18, True), 4, 6)
    for i, nn in enumerate(NATIONS):
        gp = mk(unreal.GridPanel, 'Nation_%d' % i); vadd(gp, 0, 4)
        gp.set_visibility(unreal.SlateVisibility.VISIBLE if i == 0 else unreal.SlateVisibility.COLLAPSED)
        def gadd(w, r, c):
            s = gp.add_child_to_grid(w, r, c); s.set_padding(unreal.Margin(3, 3, 3, 3)); return s
        gadd(txt('H%d_class' % i, '병과', 17, True), 0, 0)
        for k in range(3): gadd(txt('H%d_rank%d' % (i, k), '%d순위' % (k + 1), 17, True), 0, k + 1).set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
        for c, cn in enumerate(CLASSES):
            gadd(txt('C%d_%d' % (i, c), cn, 18, True), c + 1, 0).set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
            for k in range(3):
                wn = W[nn][c][k]
                b = mk(unreal.Button, 'Btn_%d_%d_%d' % (i, c, k)); b.set_is_enabled(False); b.set_tool_tip_text(unreal.Text('%s / %s / %d순위: %s (아직 추가 안 됨)' % (nn, cn, k + 1, wn)))
                b.add_child(txt('Txt_%d_%d_%d' % (i, c, k), wn, 17))
                sb = mk(unreal.SizeBox, 'Box_%d_%d_%d' % (i, c, k)); sb.set_width_override(290); sb.set_height_override(44); sb.add_child(b)
                gadd(sb, c + 1, k + 1)
    vadd(txt('Slot2Head', '2번 무기 (근접: 삽 / 칼 등)  -  비어 있음', 18, True), 12, 4)
    vadd(txt('Current', '현재 선택  1번: 없음   /   2번: 없음', 15), 6, 0)
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False)); R['n_old'] = len(R['log']); R['log'] = R['log'][:5]
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_widget2.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WM2', R.get('status'), R.get('error', '')[-300:])
