"""헤드리스: Tab 키를 쓰는 곳 찾기 - 모든 InputMappingContext 의 Tab 매핑 + 푸리나 폰 이벤트 그래프의 Tab 관련 노드 -> Data/lyra_tab_dump.json"""
import unreal, json, traceback
R = {'imc': [], 'nodes': {}}
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputMappingContext')], recursive_classes=True, package_paths=['/Game', '/ShooterCore', '/TopDownArena', '/ShooterMaps'], recursive_paths=True)
    for ad in ar.get_assets(flt):
        imc = ad.get_asset(); path = str(ad.package_name)
        try: maps = imc.get_editor_property('default_key_mappings').get_editor_property('mappings')
        except Exception:
            try: maps = imc.get_editor_property('mappings')
            except Exception as e: R['imc'].append([path, 'ERR ' + str(e)[:80]]); continue
        for m in maps:
            k = str(m.get_editor_property('key').get_editor_property('key_name'))
            if k in ('Tab',): R['imc'].append([path, k, str(m.get_editor_property('action').get_path_name()) if m.get_editor_property('action') else None])
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    for gname in unreal.BlueprintEditorLibrary.list_graph_names(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, str(gname))
        if ed is None: continue
        for n in ed.list_all_nodes():
            t = str(n.get_node_title()).replace('\n', ' ')
            vals = [str(p.get_pin_value()) for p in n.list_all_pins()]
            if 'Tab' in t or any(v == 'Tab' or 'Key=Tab' in v or 'Invert' in v for v in vals) or 'Invert' in t:
                R['nodes'][str(gname) + ':' + n.get_name()] = {'title': t, 'pins': [[str(p.get_pin_name()), str(p.get_pin_value()), [c.get_owning_node().get_name() for c in p.list_connected_pins()]] for p in n.list_all_pins()]}
        del ed
except Exception: R['error'] = traceback.format_exc()[-1200:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_tab_dump.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_TAB_DUMP', R.get('error', 'ok')[-300:])
