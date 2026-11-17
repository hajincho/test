"""교체 시작 시 FurinaP200Tick 타이머를 재시작(확실히 동작하도록)."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {}
try:
    s0 = [v for k, v in N().items() if k.startswith('P2_SetActiveFurinaSwapping') and any(c.get_owning_node().get_name().startswith('P2_Branch') for c in v.find_execute_pin().list_connected_pins())]
    R['s0_count'] = len(s0); s0 = s0[0]
    srcs = list(s0.find_execute_pin().list_connected_pins()); s0.find_execute_pin().break_pin_links()
    tm = timer('FurinaP200Tick', 0.008, True)
    for p in srcs: link(p, tm.find_execute_pin())
    link(tm.find_then_pin(), s0.find_execute_pin())
    R['srcs'] = len(srcs)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P200_TIMER_RESTART', json.dumps(R, default=str, ensure_ascii=False))
