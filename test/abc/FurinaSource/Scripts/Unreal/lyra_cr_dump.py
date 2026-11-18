"""Lyra 에디터(`py <파일> <노드이름...> [up]`): CR_FurinaSecondary 노드의 핀 기본값과 연결을 덤프한다. `up` 을 붙이면 입력 쪽 연결 노드를 40개까지 따라간다.  -> Data/lyra_cr_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_dump.json'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; UP = 'up' in ARGS; NAMES = [a for a in ARGS if a != 'up']
R = {}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    queue = list(NAMES); seen = set()
    while queue and len(seen) < 40:
        nm = queue.pop(0)
        if nm in seen: continue
        seen.add(nm); n = N.get(nm)
        if n is None: R[nm] = None; continue
        row = {'title': str(n.get_node_title()) if hasattr(n, 'get_node_title') else '', 'pins': {}}
        for p in n.get_pins():
            nm2 = str(p.get_name()); srcs = [str(s.get_pin_path()) for s in p.get_linked_source_pins()]
            dst = [str(s.get_pin_path()) for s in p.get_linked_target_pins()]
            row['pins'][nm2] = {'val': str(p.get_default_value())[:140], 'src': srcs, 'dst': dst[:6]}
            if UP:
                for s in srcs: queue.append(s.split('.')[0])
        R[nm] = row
    del N, g
try: run()
except Exception: R['error'] = traceback.format_exc()[-600:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_DUMP', len(R), R.get('error', ''))
import gc; gc.collect()
