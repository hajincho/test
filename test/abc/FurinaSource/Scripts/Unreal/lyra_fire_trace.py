"""Lyra 에디터: 푸리나 폰 EventGraph 에서 IA_FurinaFireRifle 입력 이벤트 노드 이후 실행 흐름(최대 12단계)을 출력 -> Data/lyra_fire_trace.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fire_trace.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = ed.list_all_nodes(); R['n_nodes'] = len(nodes)
    ev = [n for n in nodes if 'FireRifle' in n.get_name() or 'FireRifle' in str(n.get_node_title() if hasattr(n, 'get_node_title') else '')]
    R['events'] = [n.get_name() for n in ev]
    def pins(n):
        out = []
        for attr in ('list_pins', 'list_all_pins'):
            if hasattr(n, attr):
                try: return list(getattr(n, attr)())
                except Exception: pass
        return out
    R['pin_api'] = [a for a in dir(nodes[0]) if 'pin' in a.lower()][:20]
    trace = []
    for e in ev[:2]:
        cur = [e]; seen = set()
        for _ in range(12):
            nxt = []
            for n in cur:
                if n.get_name() in seen: continue
                seen.add(n.get_name()); row = {'node': n.get_name()}
                for pn in ('Started', 'Triggered', 'Completed', 'Canceled', 'then', 'Then', 'True', 'False'):
                    try:
                        p = n.find_output_pin(pn) if hasattr(n, 'find_output_pin') else None
                        if p and p.is_valid():
                            cs = p.list_connected_pins(); row[pn] = [c.get_owning_node().get_name() for c in cs]; nxt += [c.get_owning_node() for c in cs]
                    except Exception: pass
                trace.append(row)
            cur = nxt
            if not cur: break
    R['trace'] = trace
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIRE_TRACE', R.get('error', 'ok')[-200:])
