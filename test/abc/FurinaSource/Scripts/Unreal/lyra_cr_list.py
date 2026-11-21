"""헤드리스 가능: CR_FurinaSecondary 의 모든 노드(이름, 구조체 타입, 핀 기본값, 링크)를 Data/lyra_cr_list.json 에 기록 + 실행 체인(ExecutePin 순서)."""
import unreal, json, traceback
R = {}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {}
    for n in g.get_nodes():
        nm = str(n.get_node_path()); typ = type(n).__name__
        try: st = str(n.get_script_struct().get_name())
        except Exception: st = ''
        pins = []
        for p in n.get_pins():
            pins.append([str(p.get_name()), str(p.get_default_value())[:100], [str(t.get_pin_path()) for t in p.get_linked_source_pins()], [str(t.get_pin_path()) for t in p.get_linked_target_pins()]])
        N[nm] = {'cls': typ, 'struct': st, 'pins': pins}
    R['n'] = len(N); R['nodes'] = N
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_list.json', 'w', encoding='utf-8'), indent=0, default=str, ensure_ascii=False); print('LYRA_CR_LIST', R.get('n'), R.get('error', ''))
