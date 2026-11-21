"""Lyra 에디터(`py <파일> <노드이름> ...`): CR_FurinaSecondary 노드의 핀(값/링크)과 입력 연결을 덤프.  -> Data/lyra_cr_node_dump.json"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; R = {}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    for nm in ARGS:
        n = N.get(nm)
        if n is None: R[nm] = 'missing'; continue
        R[nm] = [[str(p.get_pin_path()), str(p.get_default_value())[:120], [str(t.get_pin_path()) for t in p.get_linked_source_pins()], [str(t.get_pin_path()) for t in p.get_linked_target_pins()]] for p in n.get_pins()]
except Exception: R['error'] = traceback.format_exc()[-700:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_node_dump.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_NODE_DUMP', R.get('error', ''))
