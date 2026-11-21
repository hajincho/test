"""헤드리스: 무기창 루트 CanvasPanel_0 HitTestInvisible -> SelfHitTestInvisible (자식 클릭 가능)."""
import unreal, json
R = {}
wbp = unreal.load_asset('/Game/Furina/UI/WBP_FurinaWeaponMenu'); wt = unreal.find_object(None, '/Game/Furina/UI/WBP_FurinaWeaponMenu.WBP_FurinaWeaponMenu:WidgetTree')
for o in unreal.ObjectIterator(unreal.Widget):
    if o.get_outer() == wt and o.get_name() == 'CanvasPanel_0':
        o.set_visibility(unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE); o.modify(); R['set'] = str(o.get_visibility())
unreal.BlueprintEditorLibrary.compile_blueprint(wbp); R['status'] = str(wbp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(wbp, False))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_weapon_menu_rootvis.json', 'w'), indent=1); print('WM_ROOTVIS', R)
