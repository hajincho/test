"""사격 FX 이벤트에서도 FurinaP200Tick 타이머를 (재)시작 -> 슬라이드 애니메이션이 항상 구동되도록."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {}
try:
    ev = node('P2_Ev_Fx'); first = ev.find_then_pin().list_connected_pins()[0]
    ev.find_then_pin().break_pin_links()
    tm = timer('FurinaP200Tick', 0.008, True)
    link(ev.find_then_pin(), tm.find_execute_pin()); link(tm.find_then_pin(), first)
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P200_TIMER_FX', json.dumps(R, default=str, ensure_ascii=False))
