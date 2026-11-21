"""헤드리스: WBP_FurinaWeaponMenu 버튼 글자/툴팁에서 '†' 제거.  -> Data/lyra_weapon_menu_nodagger.json"""
import unreal, json, traceback
FULL = '/Game/Furina/UI/WBP_FurinaWeaponMenu'; R = {'changed': []}
try:
    wbp = unreal.load_asset(FULL); wt = unreal.find_object(None, FULL + '.WBP_FurinaWeaponMenu:WidgetTree')
    for o in unreal.ObjectIterator(unreal.Widget):
        if o.get_outer() != wt or o.get_name().startswith('Old'): continue
        if isinstance(o, unreal.TextBlock):
            t = str(o.get_text())
            if '†' in t: o.set_text(unreal.Text(t.replace(' †', '').replace('†', ''))); R['changed'].append([o.get_name(), t])
        tt = str(o.get_editor_property('tool_tip_text'))
        if '†' in tt: o.set_tool_tip_text(unreal.Text(tt.replace(' †', '').replace('†', '')))
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_weapon_menu_nodagger.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('WM_NODAGGER', R.get('status'))
