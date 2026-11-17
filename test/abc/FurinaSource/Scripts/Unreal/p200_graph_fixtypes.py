"""변수 타입을 int -> double 로 바꾼 뒤 오류가 난 get/set 노드를 같은 연결로 재생성."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'fixed': []}
try:
    errs = list(ed.list_nodes_with_errors())
    plan = []
    for n in errs:
        title = str(n.get_node_title()).replace('\n', ' ')
        if not (title.startswith('Get ') or title.startswith('Set ')): continue
        var = title.split(' ', 1)[1].strip()
        conns = []
        for p in n.list_all_pins():
            for c in p.list_connected_pins():
                conns.append((str(p.get_pin_name()), c.get_owning_node().get_name(), str(c.get_pin_name())))
        defaults = {str(p.get_pin_name()): str(p.get_pin_value()) for p in n.list_all_pins()}
        plan.append((n.get_name(), title.startswith('Set '), var, conns, defaults))
    ed.remove_nodes([node(x[0]) for x in plan])
    for name, is_set, var, conns, defaults in plan:
        nn = ed.add_set_member_variable_node(var, CLS) if is_set else ed.add_get_member_variable_node(var, CLS)
        nn.rename(name)
        for mine, other, otherpin in conns:
            o = node(other); assert o is not None, 'missing ' + other
            mp = nn.find_output_pin(mine) if nn.find_output_pin(mine) is not None and nn.find_output_pin(mine).is_valid() else nn.find_input_pin(mine)
            op = o.find_output_pin(otherpin) if o.find_output_pin(otherpin) is not None and o.find_output_pin(otherpin).is_valid() else o.find_input_pin(otherpin)
            if mp.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_OUTPUT: link(mp, op)
            else: link(op, mp)
        if is_set:
            p = nn.find_input_pin(var)
            if p is not None and p.is_valid() and not p.list_connected_pins() and defaults.get(var) not in (None, ''): fval(p, float(defaults[var]))
        R['fixed'].append([name, var, len(conns)])
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name() for x in ed.list_nodes_with_errors()][:12]
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P200_FIXTYPES', json.dumps(R, default=str, ensure_ascii=False)[:2500])
