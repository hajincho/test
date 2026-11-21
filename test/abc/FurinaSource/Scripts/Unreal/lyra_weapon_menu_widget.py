"""헤드리스: 개발자용 무기 선택창 위젯 /Game/Furina/UI/WBP_FurinaWeaponMenu 생성(버튼 + 텍스트만).
 표: 행 = 병과 7, 열 = 국가 6 (모두 1번 주무기). 버튼 이름 Btn_<병과번호>_<국가번호>, 아직 무기가 없으니 전부 비활성(IsEnabled=false).
 나중에 무기를 넣을 때 해당 버튼을 활성 + OnClicked 연결.  2번(근접) 은 '비어 있음' 텍스트.  -> Data/lyra_weapon_menu_widget.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
PATH = '/Game/Furina/UI'; NAME = 'WBP_FurinaWeaponMenu'
CLASSES = ['장교', '보병', '돌격병', '대전차병', '중화기병', '저격수', '기갑병']
NATIONS = ['독일', '일본', '이탈리아', '미국', '소련', '영국']
WEAPONS = [['P38', '남부 14식', 'Beretta M34', 'M1911A1', 'TT-33', 'Enfield No.2'],
           ['Kar98k', '38식', 'Carcano M91', 'M1 Garand', 'Mosin M91/30', 'Lee-Enfield No.4'],
           ['MP40', '38식 소총', 'M38A', 'Thompson', 'PPSh-41', 'Sten Mk II'],
           ['Panzerfaust', '94식 37mm포', '47/32', 'Bazooka', 'PTRD-41', 'PIAT'],
           ['MG42', '96식', 'Breda M30', 'BAR', 'DP-27', 'Bren'],
           ['Kar98k ZF39', '97식 저격총', 'Carcano M91*', 'M1903A4', 'Mosin PU', 'No.4 Mk I(T)'],
           ['P38', '남부 14식', 'Beretta M34', 'M1911A1', 'TT-33', 'Enfield No.2']]
R = {'log': []}
def run():
    at = unreal.AssetToolsHelpers.get_asset_tools(); full = PATH + '/' + NAME
    if unreal.EditorAssetLibrary.does_asset_exist(full): unreal.EditorAssetLibrary.delete_asset(full)
    # 새 위젯 BP 는 루트 패널을 파이썬으로 지정할 수 없어서, 그래프가 비어 있고 루트가 CanvasPanel 인 번들 위젯을 복제해 내용만 바꾼다
    wbp = unreal.EditorAssetLibrary.duplicate_asset('/Game/3DPlatformerGameBundle/Widgets/GrindRailGuideWidgetBP/Guide_Widget_WBP', full)
    wt = unreal.find_object(None, full + '.' + NAME + ':WidgetTree'); R['wt'] = str(wt)
    roots = [o for o in unreal.ObjectIterator(unreal.PanelWidget) if o.get_outer() == wt and o.get_parent() is None]; R['roots'] = [o.get_name() for o in roots]
    def mk(cls, nm): return unreal.new_object(cls, outer=wt, name=nm)
    def txt(nm, s, size=12, bold=False):
        t = mk(unreal.TextBlock, nm); t.set_text(unreal.Text(s))
        f = t.get_editor_property('font'); f.set_editor_property('size', size)
        if bold: f.set_editor_property('typeface_font_name', 'Bold')
        t.set_editor_property('font', f); return t
    root = [o for o in roots if isinstance(o, unreal.CanvasPanel)][0]; R['old_children'] = [c.get_name() for c in root.get_all_children()]; root.clear_children()
    bd = mk(unreal.Border, 'Panel'); bd.set_editor_property('brush_color', unreal.LinearColor(0.02, 0.02, 0.03, 0.88)); bd.set_editor_property('padding', unreal.Margin(16, 16, 16, 16))
    cs = root.add_child_to_canvas(bd)
    cs.set_anchors(unreal.Anchors(unreal.Vector2D(0.5, 0.5), unreal.Vector2D(0.5, 0.5))); cs.set_alignment(unreal.Vector2D(0.5, 0.5)); cs.set_auto_size(True); cs.set_position(unreal.Vector2D(0, 0))
    vb = mk(unreal.VerticalBox, 'VBox'); bd.add_child(vb)
    vb.add_child_to_vertical_box(txt('Title', '무기 선택 (개발자용)    Tab: 닫기', 18, True))
    vb.add_child_to_vertical_box(txt('Slot1Head', '1번 무기 (주무기)  -  회색 버튼은 아직 추가되지 않은 무기', 12, True))
    gp = mk(unreal.GridPanel, 'Grid'); vb.add_child_to_vertical_box(gp)
    def gadd(w, r, c):
        s = gp.add_child_to_grid(w, r, c); s.set_padding(unreal.Margin(2, 2, 2, 2)); return s
    gadd(txt('HeadCorner', '병과 \\ 국가', 12, True), 0, 0)
    for n, nn in enumerate(NATIONS): gadd(txt('HeadN%d' % n, nn, 12, True), 0, n + 1).set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
    for c, cn in enumerate(CLASSES):
        gadd(txt('HeadC%d' % c, cn, 12, True), c + 1, 0).set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        for n in range(len(NATIONS)):
            b = mk(unreal.Button, 'Btn_%d_%d' % (c, n)); b.set_is_enabled(False)
            b.set_tool_tip_text(unreal.Text('%s / %s / %s (아직 추가 안 됨)' % (cn, NATIONS[n], WEAPONS[c][n])))
            sb = mk(unreal.SizeBox, 'Box_%d_%d' % (c, n)); sb.set_width_override(130); sb.add_child(b)
            b.add_child(txt('Txt_%d_%d' % (c, n), WEAPONS[c][n], 11))
            gadd(sb, c + 1, n + 1)
    vb.add_child_to_vertical_box(txt('Slot2Head', '2번 무기 (근접: 삽 / 칼 등)  -  비어 있음', 12, True)).set_padding(unreal.Margin(0, 12, 0, 4))
    vb.add_child_to_vertical_box(txt('Current', '현재 선택  1번: 없음   /   2번: 없음', 11)).set_padding(unreal.Margin(0, 8, 0, 0))
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp)
    R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    R['n_widgets'] = len(wt.get_all_widgets()) if hasattr(wt, 'get_all_widgets') else None
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_weapon_menu_widget.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_WEAPON_MENU_WIDGET', R.get('status'), R.get('error', '')[-400:])
