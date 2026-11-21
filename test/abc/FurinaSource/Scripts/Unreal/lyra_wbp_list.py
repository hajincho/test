import unreal, json, traceback
R = []
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/UMGEditor', 'WidgetBlueprint')], package_paths=['/Game/3DPlatformerGameBundle', '/Game/Furina', '/Game/TFPMovement'], recursive_paths=True)
    for ad in ar.get_assets(flt)[:40]:
        path = str(ad.package_name); nm = str(ad.asset_name)
        bp = ad.get_asset(); wt = unreal.find_object(None, path + '.' + nm + ':WidgetTree')
        ws = [o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt]
        roots = [o.get_class().get_name() + ':' + o.get_name() for o in ws if o.get_parent() is None]
        try: par = str(bp.get_editor_property('parent_class').get_name())
        except Exception: par = '?'
        ng = 0
        try:
            ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); ng = len(ed.list_all_nodes()) if ed else -1
        except Exception: ng = -2
        R.append([path, par, len(ws), roots, ng])
except Exception: R.append(traceback.format_exc()[-600:])
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_wbp_list.json', 'w'), indent=1); print('WBP_LIST_OK')
