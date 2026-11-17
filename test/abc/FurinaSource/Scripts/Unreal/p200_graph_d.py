"""2단계 D: 권총일 때 총알/탄피를 다른 클래스로 스폰 (SelectClass 는 Actor 클래스 핀에 연결되지 않아 분기 + 별도 스폰 노드로 구현)."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-900:]])
def pistol(): return is_active('FurinaPistolOn')
def bullet():
    old = [n for k, n in N().items() if k.startswith('P2_SelBulletCls') or k.startswith('P2_SelCaseCls')]
    if old: ed.remove_nodes(old)
    aim = node('K2Node_FPF_Aim'); old_t = list(aim.find_then_pin().list_connected_pins()); aim.find_then_pin().break_pin_links()
    b = branch(pistol()); link(aim.find_then_pin(), b.find_execute_pin())
    for p in old_t: link(b.find_else_pin(), p)
    sp = ed.create_node_from_name('Game|SpawnActorfromClass', unreal.Vector2D(3000, 7600), []); assert sp, 'spawn node'; sp.rename(uniq('SpawnP220Bullet'))
    sp.find_input_pin('Class').set_pin_value('/Game/Furina/P200/BP_P220Bullet.BP_P220Bullet_C')
    link(node('K2Node_FPF_ShotXf').find_result_pin(), sp.find_input_pin('SpawnTransform'))
    sp.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn')
    me = node('K2Node_FPF_Self').find_self_pin(); link(me, sp.find_input_pin('Owner')); link(me, sp.find_input_pin('Instigator'))
    link(b.find_then_pin(), sp.find_execute_pin()); link(sp.find_then_pin(), node('K2Node_FPF_Recoil').find_execute_pin())
    return ['bullet ok', str(sp.find_input_pin('Class').get_pin_value())[:70], [str(p.get_pin_name()) for p in sp.list_all_pins()]]
def case():
    shell = node('FNS_SetUseShell'); old_t = list(shell.find_then_pin().list_connected_pins()); shell.find_then_pin().break_pin_links()
    b = branch(pistol()); link(shell.find_then_pin(), b.find_execute_pin())
    for p in old_t: link(b.find_else_pin(), p)
    xf = node('M4_CaseTransform').find_result_pin()
    d = fn('/Script/Engine.GameplayStatics:BeginDeferredActorSpawnFromClass', 'CaseP220Begin')
    d.find_input_pin('ActorClass').set_pin_value('/Game/Furina/P200/BP_P220Case.BP_P220Case_C'); link(xf, d.find_input_pin('SpawnTransform'))
    d.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn'); link(node('K2Node_Self_0').find_self_pin(), d.find_input_pin('Owner'))
    f = fn('/Script/Engine.GameplayStatics:FinishSpawningActor', 'CaseP220Finish'); link(d.find_result_pin(), f.find_input_pin('Actor')); link(xf, f.find_input_pin('SpawnTransform'))
    link(b.find_then_pin(), d.find_execute_pin()); link(d.find_then_pin(), f.find_execute_pin())
    fxb = node('M4_CaseFinish').find_then_pin().list_connected_pins()
    for p in fxb: link(f.find_then_pin(), p)
    return ['case ok', str(d.find_input_pin('ActorClass').get_pin_value())[:70], len(fxb)]
step('bullet', bullet); step('case', case)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
R['errors'] = [str(x.get_name()) for x in ed.list_nodes_with_errors()][:20]
print('P200_GRAPH_D', json.dumps(R, default=str, ensure_ascii=False)[:3500])
