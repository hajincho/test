"""변수를 double 로 바꾼 뒤 남은 자동 변환 체인(To Float(Integer) / Truncate)을 우회해 값이 정수로 잘리는 문제 제거."""
import unreal, json, re, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
try:
    CONV = ('To Float (Integer)', 'Truncate', 'To Integer', 'Round')
    Nn = N()
    cands = [n for k, n in Nn.items() if re.match(r'K2Node_CallFunction_(\d+)$', k) and int(re.match(r'K2Node_CallFunction_(\d+)$', k).group(1)) >= 100 and str(n.get_node_title()).replace('\n', ' ') in CONV]
    R['cands'] = [(c.get_name(), str(c.get_node_title())) for c in cands]
    def data_in(c):
        for p in c.list_all_pins():
            if str(p.get_pin_name()) in ('execute', 'then'): continue
            if p.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT and p.list_connected_pins(): return p.list_connected_pins()[0]
    def data_out(c):
        for p in c.list_all_pins():
            if p.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT and str(p.get_pin_name()) == 'ReturnValue': return p
    names = {c.get_name() for c in cands}
    # 체인 끝(소스가 변환 노드가 아닌 것)부터 정리: 반복해서 변환 노드를 직접 연결로 대체
    for _ in range(6):
        changed = False
        for c in cands:
            if c.get_name() not in names: continue
            src = data_in(c); out = data_out(c)
            if src is None: continue
            consumers = list(out.list_connected_pins())
            for cons in consumers: link(src, cons)
            names.discard(c.get_name()); changed = True
            R['log'].append(['bypassed', c.get_name(), len(consumers)])
        if not changed: break
    rem = [node(n) for n in [c.get_name() for c in cands] if node(n)]
    ed.remove_nodes(rem)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P200_BYPASS', json.dumps(R, default=str, ensure_ascii=False)[:3000])
