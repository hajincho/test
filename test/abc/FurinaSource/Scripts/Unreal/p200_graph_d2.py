"""2단계 D2: D 단계가 self 핀 조회 실수로 중간에 멈춘 부분을 이어서 연결 (이미 만든 분기/스폰 노드를 재사용)."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-900:]])
def selfpin(n): return n.find_output_pin('self')
def by_prefix(prefix): return [v for k, v in N().items() if k.startswith(prefix)]
def bullet():
    sps = by_prefix('P2_SpawnP220Bullet'); assert len(sps) == 1, 'spawn nodes %d' % len(sps); sp = sps[0]
    aim = node('K2Node_FPF_Aim'); b = aim.find_then_pin().list_connected_pins()[0].get_owning_node()   # 삽입해 둔 분기
    me = selfpin(node('K2Node_FPF_Self'))
    for pin in ('Owner', 'Instigator'):
        p = sp.find_input_pin(pin)
        if not p.list_connected_pins(): link(me, p)
    if not sp.find_input_pin('SpawnTransform').list_connected_pins(): link(node('K2Node_FPF_ShotXf').find_result_pin(), sp.find_input_pin('SpawnTransform'))
    sp.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn')
    if not b.find_then_pin().list_connected_pins(): link(b.find_then_pin(), sp.find_execute_pin())
    rec = node('K2Node_FPF_Recoil').find_execute_pin()
    if rec not in sp.find_then_pin().list_connected_pins(): link(sp.find_then_pin(), rec)
    return ['bullet ok', str(sp.find_input_pin('Class').get_pin_value())[:80]]
def case():
    shell = node('FNS_SetUseShell'); b = shell.find_then_pin().list_connected_pins()[0].get_owning_node()   # 삽입해 둔 분기
    xf = node('M4_CaseTransform').find_result_pin()
    ds = by_prefix('P2_CaseP220Begin'); d = ds[0] if ds else fn('/Script/Engine.GameplayStatics:BeginDeferredActorSpawnFromClass', 'CaseP220Begin')
    d.find_input_pin('ActorClass').set_pin_value('/Game/Furina/P200/BP_P220Case.BP_P220Case_C')
    if not d.find_input_pin('SpawnTransform').list_connected_pins(): link(xf, d.find_input_pin('SpawnTransform'))
    d.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn')
    if not d.find_input_pin('Owner').list_connected_pins(): link(selfpin(node('K2Node_Self_0')), d.find_input_pin('Owner'))
    fs = by_prefix('P2_CaseP220Finish'); f = fs[0] if fs else fn('/Script/Engine.GameplayStatics:FinishSpawningActor', 'CaseP220Finish')
    if not f.find_input_pin('Actor').list_connected_pins(): link(d.find_result_pin(), f.find_input_pin('Actor'))
    if not f.find_input_pin('SpawnTransform').list_connected_pins(): link(xf, f.find_input_pin('SpawnTransform'))
    if not b.find_then_pin().list_connected_pins(): link(b.find_then_pin(), d.find_execute_pin())
    if not d.find_then_pin().list_connected_pins(): link(d.find_then_pin(), f.find_execute_pin())
    fx = node('M4_CaseFinish').find_then_pin().list_connected_pins()
    for p in fx:
        if p not in f.find_then_pin().list_connected_pins(): link(f.find_then_pin(), p)
    return ['case ok', len(fx), str(d.find_input_pin('ActorClass').get_pin_value())[:80]]
step('bullet', bullet); step('case', case)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
R['errors'] = [str(x.get_name()) for x in ed.list_nodes_with_errors()][:20]
print('P200_GRAPH_D2', json.dumps(R, default=str, ensure_ascii=False)[:3500])
