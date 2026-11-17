"""자동 변환 체인(Truncate / To Float(Integer))을 체인 전체 단위로 우회: 최종 소스 -> 최종 소비자를 직접 연결 (P2_ 노드와 관련된 체인만)."""
import unreal, json, re, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
try:
    CONV = ('To Float (Integer)', 'Truncate')
    Nn = N()
    def is_conv(n): return re.match(r'K2Node_CallFunction_\d+$', n.get_name()) is not None and str(n.get_node_title()).replace('\n', ' ') in CONV
    def up(pin):   # 입력핀의 최종 소스(출력핀)
        c = pin.list_connected_pins()
        if not c: return None
        o = c[0]
        while is_conv(o.get_owning_node()):
            inp = [p for p in o.get_owning_node().list_all_pins() if p.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT and str(p.get_pin_name()) not in ('execute',) and p.list_connected_pins()]
            if not inp: return None
            o = inp[0].list_connected_pins()[0]
        return o
    used = set(); pairs = []
    for k, n in Nn.items():
        if is_conv(n): continue
        for p in n.list_all_pins():
            if p.get_pin_direction() != unreal.EdGraphPinDirection.EGPD_INPUT: continue
            c = p.list_connected_pins()
            if c and is_conv(c[0].get_owning_node()):
                srcpin = up(p)
                if srcpin is None: continue
                if not (n.get_name().startswith('P2_') or srcpin.get_owning_node().get_name().startswith('P2_')): continue
                pairs.append((srcpin, p))
    for srcpin, dst in pairs:
        # 체인 노드 수집(제거용)
        o = dst.list_connected_pins()[0]
        while is_conv(o.get_owning_node()):
            used.add(o.get_owning_node().get_name())
            inp = [q for q in o.get_owning_node().list_all_pins() if q.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT and str(q.get_pin_name()) != 'execute' and q.list_connected_pins()]
            o = inp[0].list_connected_pins()[0]
        before = len(N()); dst.break_pin_links()
        ok = PL.try_create_connection(srcpin, dst)
        R['log'].append([srcpin.get_owning_node().get_name()[:26] + '.' + str(srcpin.get_pin_name()), dst.get_owning_node().get_name()[:26] + '.' + str(dst.get_pin_name()), ok, len(N()) - before])
    # 남은 연결이 없는 변환 노드 제거
    dead = [node(nm) for nm in used if node(nm) and not any(p.list_connected_pins() for p in node(nm).list_all_pins() if p.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT)]
    ed.remove_nodes(dead); R['removed'] = len(dead); R['pairs'] = len(pairs)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
    R['conv_left_p2'] = [n.get_name() for k, n in N().items() if is_conv(n)][:30]
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P200_BYPASS2', json.dumps(R, default=str, ensure_ascii=False)[:3500])
