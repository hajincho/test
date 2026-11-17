"""폰 그래프: 권총 장착 시 Lyra 권총 애니 재생 (DefaultSlot 동적 몽타주).
 - 장착(SwapMid, 권총): Equip 1회 -> 1.35초 뒤 Hold(대기 루프)   - 해제(소총 복귀): 슬롯 애니 정지
 - 재장전(권총): Reload 몽타주 -> 2.05초 뒤 Hold 복귀            - 사격(권총): 소총용 킥 몽타주 생략
 이벤트: FurinaPistolHold (타이머 호출)"""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
A = '/Game/Furina/P220/Anim/'
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-800:]])
def pistol(): return is_active('FurinaPistolOn')
def anim_inst():
    g = comp_get('FurinaMesh'); a = fn('/Script/Engine.SkeletalMeshComponent:GetAnimInstance', 'GetAnimInst'); link(g, a.find_self_pin()); return a.find_result_pin()
def play(seq, loops):
    n = fn('/Script/Engine.AnimInstance:PlaySlotAnimationAsDynamicMontage', 'PlaySlot'); link(anim_inst(), n.find_self_pin())
    n.find_input_pin('Asset').set_pin_value(A + seq + '.' + seq); n.find_input_pin('SlotNodeName').set_pin_value('DefaultSlot')
    fval(n.find_input_pin('BlendInTime'), 0.2); fval(n.find_input_pin('BlendOutTime'), 0.2); fval(n.find_input_pin('InPlayRate'), 1.0)
    n.find_input_pin('LoopCount').set_pin_value(str(loops)); fval(n.find_input_pin('BlendOutTriggerTime'), -1.0); fval(n.find_input_pin('InTimeToStartMontageAt'), 0.0); return n
def stop():
    n = fn('/Script/Engine.AnimInstance:StopSlotAnimation', 'StopSlot'); link(anim_inst(), n.find_self_pin()); fval(n.find_input_pin('InBlendOutTime'), 0.2); n.find_input_pin('SlotNodeName').set_pin_value('DefaultSlot'); return n
def hold_event():
    ev = ed.add_custom_event_node('FurinaPistolHold'); ev.rename('P2_Ev_Hold')
    b = branch(pistol()); link(ev.find_then_pin(), b.find_execute_pin()); p = play('Furina_Pistol_Idle_Hipfire', 9999); link(b.find_then_pin(), p.find_execute_pin()); return 'hold ev'
def swap():
    mags = [v for k, v in N().items() if k.startswith('P2_SetMagMesh')]; assert len(mags) == 2, len(mags)
    to_p = [m for m in mags if str(m.find_input_pin('NewMesh').get_pin_value()) in ('None', '')][0]; to_r = [m for m in mags if m is not to_p][0]
    nxt = list(to_p.find_then_pin().list_connected_pins()); to_p.find_then_pin().break_pin_links(); to_r.find_then_pin().break_pin_links()
    eq = play('Furina_Pistol_Equip', 1); tm = timer('FurinaPistolHold', 1.35)
    link(to_p.find_then_pin(), eq.find_execute_pin()); link(eq.find_then_pin(), tm.find_execute_pin())
    st = stop(); link(to_r.find_then_pin(), st.find_execute_pin())
    for p in nxt:
        link(tm.find_then_pin(), p); link(st.find_then_pin(), p)
    return 'swap ok %d' % len(nxt)
def reload():
    old = node('M4_ReloadTimer'); old_t = list(old.find_then_pin().list_connected_pins()); old.find_then_pin().break_pin_links()
    b = branch(pistol()); link(old.find_then_pin(), b.find_execute_pin())
    for p in old_t: link(b.find_else_pin(), p)
    rl = play('Furina_Pistol_Reload', 1); tm = timer('FurinaPistolHold', 2.05)
    link(b.find_then_pin(), rl.find_execute_pin()); link(rl.find_then_pin(), tm.find_execute_pin())
    after = node('K2Node_FP_ReloadRifle').find_execute_pin(); link(tm.find_then_pin(), after)
    return 'reload ok'
def fire():
    fa = node('K2Node_FPF_FaceAim'); old_t = list(fa.find_then_pin().list_connected_pins()); fa.find_then_pin().break_pin_links()
    b = branch(pistol()); link(fa.find_then_pin(), b.find_execute_pin())
    for p in old_t: link(b.find_else_pin(), p)
    link(b.find_then_pin(), node('K2Node_FPF_Bolt').find_execute_pin()); return 'fire ok'
for n, f in (('hold_event', hold_event), ('swap', swap), ('reload', reload), ('fire', fire)): step(n, f)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
print('P220_GRAPH_ANIM', json.dumps(R, default=str, ensure_ascii=False)[:3000])
