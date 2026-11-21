"""헤드리스: 무기창 위젯 가시성 HitTestInvisible(복제한 번들 안내 위젯 설정이 남음) -> Visible (클릭/포커스 가능). 활성화 시 가시성도 Visible.  -> Data/lyra_weapon_menu_visible.json"""
import unreal, json, traceback
R = {}
try:
    wbp = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu'); cdo = unreal.get_default_object(wbp.generated_class())
    R['before'] = str(cdo.get_visibility())
    cdo.set_editor_property('visibility', unreal.SlateVisibility.VISIBLE)
    for pn, v in (('activated_visibility', unreal.SlateVisibility.VISIBLE), ('set_visibility_on_activated', True)):
        try: R[pn + '_before'] = str(cdo.get_editor_property(pn)); cdo.set_editor_property(pn, v)
        except Exception as e: R[pn + '_err'] = str(e)[:120]
    unreal.BlueprintEditorLibrary.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status'))
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
    c2 = unreal.get_default_object(wbp.generated_class()); R['after'] = str(c2.get_visibility())
    wt = unreal.find_object(None, '/Game/Furina/UI/WBP_FurinaWeaponMenu.WBP_FurinaWeaponMenu:WidgetTree')
    R['tree_vis'] = {o.get_name(): str(o.get_visibility()) for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt and o.get_name() in ('CanvasPanel_0', 'Panel', 'VBox', 'TabRow', 'Tab_0', 'Nation_0')}
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_weapon_menu_visible.json', 'w'), indent=1); print('WM_VIS', R.get('status'))
