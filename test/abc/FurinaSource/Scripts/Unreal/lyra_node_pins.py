"""Lyra 에디터(`py <파일> <노드이름> [노드이름...]`): ThirdPersonCharacter_BP EventGraph 노드의 메서드/핀 이름, 핀 기본값, 연결을 덤프 -> Data/lyra_node_pins.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_node_pins.json'
NAMES = [a for a in sys.argv[1:] if not a.endswith('.py')]
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); allnodes = {n.get_name(): n for n in ed.list_all_nodes()}
    UP = 'up' in sys.argv; NAMES = [x for x in NAMES if x != 'up']; queue = list(NAMES); seen = set()
    while queue:
        nm = queue.pop(0)
        if nm in seen: continue
        seen.add(nm); n = allnodes.get(nm)
        if n is None: R[nm] = None; continue
        row = {'cls': n.get_class().get_name(), 'methods': [m for m in dir(n) if not m.startswith('_') and ('pin' in m.lower())][:30]}
        pins = []
        for getter in ('list_all_pins',):
            if hasattr(n, getter):
                try: pins = list(getattr(n, getter)()); row['via'] = getter; break
                except Exception as e: row['err_' + getter] = str(e)[:60]
        row['pins'] = []
        for p in pins:
            d = {'name': str(p.get_pin_name()), 'dir': str(p.get_pin_direction())}
            for g in ('get_pin_value', 'get_pin_type_display_string'):
                if hasattr(p, g):
                    try: d[g] = str(getattr(p, g)())[:120]
                    except Exception: pass
            try: d['conn'] = [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()]
            except Exception: pass
            row['pins'].append(d)
        R[nm] = row
        if UP and len(seen) < 30:
            for p in pins:
                if 'INPUT' in str(p.get_pin_direction()).upper() and 'exec' not in str(p.get_pin_name()).lower():
                    for c in p.list_connected_pins(): queue.append(c.get_owning_node().get_name())
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_NODE_PINS', len(NAMES), R.get('error', '')[-200:])

for _n in ('bp', 'ed', 'allnodes', 'nodes', 'ev', 'chain', 'cur', 'nxt', 'n', 'p', 'pins', 'queue', 'row'):   # 블루프린트/노드 래퍼를 전역에 남기면 다음 GC 에서 에디터가 죽는다
    globals().pop(_n, None)
import gc; gc.collect()
