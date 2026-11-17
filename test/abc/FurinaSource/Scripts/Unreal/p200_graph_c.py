"""2단계 C: 총알/탄피 클래스 선택 (SelectClass 핀 이름은 bSelectA)."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {}
try:
    old = [n for k, n in N().items() if k.startswith('P2_SelBulletCls') or k.startswith('P2_SelCaseCls')]
    if old: ed.remove_nodes(old)
    def pistol(): return is_active('FurinaPistolOn')
    def sel(prefix, a, b):
        s = fn(KML + 'SelectClass', prefix); s.find_input_pin('A').set_pin_value(a); s.find_input_pin('B').set_pin_value(b); link(pistol(), s.find_input_pin('bSelectA')); return s
    sb = sel('SelBulletCls', '/Game/Furina/P200/BP_P220Bullet.BP_P220Bullet_C', '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    link(sb.find_result_pin(), node('K2Node_FPF_Spawn').find_input_pin('Class'))
    sc = sel('SelCaseCls', '/Game/Furina/P200/BP_P220Case.BP_P220Case_C', '/Game/Furina/M4/BP_223Case.BP_223Case_C')
    link(sc.find_result_pin(), node('M4_CaseSpawn').find_input_pin('ActorClass'))
    R['sel_a'] = str(sb.find_input_pin('A').get_pin_value()); R['sel_b'] = str(sb.find_input_pin('B').get_pin_value())
    R['spawn_class_links'] = [c.get_owning_node().get_name() for c in node('K2Node_FPF_Spawn').find_input_pin('Class').list_connected_pins()]
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['spawn_pins'] = [str(p.get_pin_name()) for p in node('K2Node_FPF_Spawn').list_all_pins()]
    R['errors'] = [str(x.get_name()) for x in ed.list_nodes_with_errors()][:20]
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P200_GRAPH_C', json.dumps(R, default=str, ensure_ascii=False)[:2500])
