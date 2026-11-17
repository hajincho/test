"""Lyra 에디터: RightMouseButton / Two / One 에 묶인 모든 IMC 매핑(액션, consume, 트리거)과 푸리나 폰의 Weapon2 입력 이벤트 이후 실행 흐름 -> Data/lyra_rmb_scan.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_rmb_scan.json'
R = {'imcs': [], 'default_imc_order': []}
KEYS = ('RightMouseButton', 'Two', 'One')
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputMappingContext'), True):
        imc = a.get_asset(); hits = []
        for i, m in enumerate(imc.get_editor_property('default_key_mappings').get_editor_property('mappings')):
            k = str(m.get_editor_property('key').get_editor_property('key_name')); ia = m.get_editor_property('action')
            if k in KEYS and ia:
                hits.append([i, k, ia.get_name(), 'consume=' + str(ia.get_editor_property('consume_input')), 'trig=' + str([t.get_class().get_name() for t in ia.get_editor_property('triggers')]), 'mtrig=' + str([t.get_class().get_name() for t in m.get_editor_property('triggers')])])
        if hits: R['imcs'].append({'imc': str(a.get_editor_property('package_name')), 'hits': hits})
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = ed.list_all_nodes()
    ev = [n for n in nodes if any(k in n.get_name() for k in ('Weapon2', 'FireMode', 'FPW2', 'Weapon1'))]
    R['weapon_events'] = [n.get_name() for n in ev]
    trace = []
    for e in ev[:6]:
        cur = [e]; seen = set()
        for _ in range(10):
            nxt = []
            for n in cur:
                if n.get_name() in seen: continue
                seen.add(n.get_name()); row = {'from': e.get_name(), 'node': n.get_name()}
                for pn in ('Started', 'Triggered', 'Completed', 'then', 'Then', 'True', 'False'):
                    try:
                        p = n.find_output_pin(pn)
                        if p and p.is_valid():
                            cs = p.list_connected_pins(); row[pn] = [c.get_owning_node().get_name() for c in cs]; nxt += [c.get_owning_node() for c in cs]
                    except Exception: pass
                trace.append(row)
            cur = nxt
            if not cur: break
    R['trace'] = trace
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RMB_SCAN', len(R['imcs']), R.get('error', '')[-200:])
