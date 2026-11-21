"""Lyra 에디터(`py <파일> <시작노드> [최대개수]`): CR_FurinaSecondary 의 실행 선(ExecutePin)을 시작 노드부터 따라가며 노드 이름/제목/Item/Weight 연결을 기록.  -> Data/lyra_cr_exec_chain.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_exec_chain.json'
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; START = ARGS[0] if ARGS else 'RLArmIK'; MAXN = int(ARGS[1]) if len(ARGS) > 1 else 80
R = {'chain': []}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    cur = START; seen = set()
    while cur and cur in N and cur not in seen and len(R['chain']) < MAXN:
        seen.add(cur); n = N[cur]; row = {'node': cur, 'title': str(n.get_node_title())}
        nxt = []
        for p in n.get_pins():
            nm = str(p.get_name())
            if nm == 'ExecutePin': nxt = [str(t.get_pin_path()).split('.')[0] for t in p.get_linked_target_pins()]
            if nm in ('Item', 'Weight', 'Space') or nm.startswith('Item'):
                row[nm] = [str(p.get_default_value())[:60], [str(s.get_pin_path()) for s in p.get_linked_source_pins()]]
        R['chain'].append(row); row['next'] = nxt
        cur = nxt[0] if nxt else None
    del N, g
try: run()
except Exception: R['error'] = traceback.format_exc()[-600:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_EXEC_CHAIN', len(R['chain']), R.get('error', ''))
import gc; gc.collect()
