"""Lyra 에디터(`py <파일> [단계]`, PIE 중지 상태): 노리쇠 후퇴 + 긴급 재장전 분기를 ThirdPersonCharacter_BP 에 넣는다. 단계: comp / vars / tick / kick / reload (생략하면 전부). 각 단계는 이미 있으면 건너뛴다.
 comp  : 컴포넌트 FurinaBolt(SM_M4Bolt, 부모 FurinaRifle, 소총과 같은 위치), 렌더 설정은 FurinaMag 에서 복사
 vars  : 실수 변수 FurinaBoltKick(발사 때 1로 올라가 0.06초에 걸쳐 0으로 감소), FurinaBoltHold(걸림 상태 0~1)
 tick  : FurinaMagUpdate(0.016초 타이머) 맨 앞에 노리쇠 계산을 넣는다
         걸림 목표 = 재장전 중이면 곡선 BoltBack, 아니면 (잔탄 <= 0 ? 1 : 0)  -> FurinaBoltHold 로 FInterpTo(속도 35)
         위치 = max(FurinaBoltHold, sin(pi x (1 - FurinaBoltKick))) x -7cm (총 앞쪽 +Y 기준 뒤로)  -> FurinaBolt.SetRelativeLocation,  권총 장착 중이면 숨김
 kick  : FurinaRifleShot 에서 M4_SetFurinaAmmo 바로 뒤에 FurinaBoltKick = 1
 reload: 재장전 요청에서 소총이고 잔탄 <= 0 이면 몽타주 AM_Furina_FP_ReloadEmpty, 타이머 2.0초 (그 외엔 기존 AM_Furina_FP_Reload 3.0초)
   노드 이름: FBT_*   -> Data/lyra_bolt_graph.json"""
import unreal, json, sys, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bolt_graph.json'
STEPS = [a for a in sys.argv[1:] if a in ('comp', 'vars', 'tick', 'kick', 'reload')] or ['comp', 'vars', 'tick', 'kick', 'reload']
STROKE = 7.0
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'steps': STEPS, 'log': [], 'prog': []}
def prog(m):
    R['prog'].append(m); json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
bp = unreal.load_asset(PAWN)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
def pin(n, name, out=False):
    p = n.find_output_pin(name) if out else n.find_input_pin(name)
    assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
def link(a, b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(), ('link: 핀이 없음', a, b)
    assert CONN(a, b), ('link', a.get_owning_node().get_name(), a.get_pin_name(), '->', b.get_owning_node().get_name(), b.get_pin_name())
def step_comp():
    if 'FurinaBolt' in handles(): return 'exists'
    h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaRifle'], new_class=unreal.StaticMeshComponent, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text('FurinaBolt'))
    b = comp('FurinaBolt'); m = comp('FurinaMag'); b.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/M4/SM_M4Bolt'))
    b.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); b.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=0, yaw=0)); b.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
    b.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    copied = []
    for pn in ('cast_shadow', 'render_in_main_pass', 'render_in_depth_pass', 'owner_no_see', 'only_owner_see', 'visible', 'hidden_in_game', 'cast_contact_shadow', 'cast_dynamic_shadow', 'receives_decals', 'visible_in_ray_tracing', 'lighting_channels', 'cast_hidden_shadow', 'use_as_occluder'):
        try: b.set_editor_property(pn, m.get_editor_property(pn)); copied.append(pn)
        except Exception: pass
    return ['added', copied]
def step_vars():
    existing = [str(x) for x in BEL.list_member_variable_names(bp)]; out = []
    for name in ('FurinaBoltKick', 'FurinaBoltHold'):
        if name in existing: out.append(name + ':exists'); continue
        out.append([name, BEL.add_member_variable(bp, name, BEL.get_basic_type_by_name('real'))])
    return out
def graph():
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); return ed, {n.get_name(): n for n in ed.list_all_nodes()}
def fn(ed, name, path, **vals):
    n = ed.add_call_function_node(path); assert n, path; n.rename(name)
    for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
    return n
def step_tick():
    ed, N = graph()
    if 'FBX_SetLoc' in N: return 'exists'
    K = '/Script/Engine.KismetMathLibrary:'
    def getv(name, var): n = ed.add_get_member_variable_node(var); n.rename(name); return n
    def setv(name, var): n = ed.add_set_member_variable_node(var); n.rename(name); return n
    # 1) kick 감소 후 저장
    kick0 = getv('FBX_Kick0', 'FurinaBoltKick'); dec = fn(ed, 'FBX_KickDec', K + 'Subtract_DoubleDouble'); mx = fn(ed, 'FBX_KickMax', K + 'FMax')
    link(pin(kick0, 'FurinaBoltKick', True), pin(dec, 'A')); pin(dec, 'B').set_pin_value('0.2667'); link(pin(dec, 'ReturnValue', True), pin(mx, 'A')); pin(mx, 'B').set_pin_value('0.0')
    setk = setv('FBX_SetKick', 'FurinaBoltKick'); link(pin(mx, 'ReturnValue', True), pin(setk, 'FurinaBoltKick'))
    # 2) 걸림 목표와 보간
    ammo = getv('FBX_Ammo', 'FurinaAmmo'); le = fn(ed, 'FBX_AmmoLe0', K + 'LessEqual_IntInt', B=0); link(pin(ammo, 'FurinaAmmo', True), pin(le, 'A'))
    t0 = fn(ed, 'FBX_T0', K + 'SelectFloat', A=1.0, B=0.0); link(pin(le, 'ReturnValue', True), pin(t0, 'bPickA'))
    curve = fn(ed, 'FBX_Curve', '/Script/Engine.AnimInstance:GetCurveValue', CurveName='BoltBack'); link(pin(N['FMG_Anim'], 'ReturnValue', True), curve.find_self_pin())
    rl = getv('FBX_Reloading', 'FurinaReloading'); t1 = fn(ed, 'FBX_Target', K + 'SelectFloat'); link(pin(rl, 'FurinaReloading', True), pin(t1, 'bPickA'))
    link(pin(curve, 'ReturnValue', True), pin(t1, 'A')); link(pin(t0, 'ReturnValue', True), pin(t1, 'B'))
    hold0 = getv('FBX_Hold0', 'FurinaBoltHold'); ip = fn(ed, 'FBX_Interp', K + 'FInterpTo', DeltaTime=0.016, InterpSpeed=35.0)
    link(pin(hold0, 'FurinaBoltHold', True), pin(ip, 'Current')); link(pin(t1, 'ReturnValue', True), pin(ip, 'Target'))
    seth = setv('FBX_SetHold', 'FurinaBoltHold'); link(pin(ip, 'ReturnValue', True), pin(seth, 'FurinaBoltHold'))
    # 3) 위치 = max(hold, sin(pi (1-kick))) x -STROKE
    kick1 = getv('FBX_Kick1', 'FurinaBoltKick'); om = fn(ed, 'FBX_OneMinus', K + 'Subtract_DoubleDouble'); link(pin(kick1, 'FurinaBoltKick', True), pin(om, 'B')); pin(om, 'A').set_pin_value('1.0')
    mp = fn(ed, 'FBX_MulPi', K + 'Multiply_DoubleDouble'); link(pin(om, 'ReturnValue', True), pin(mp, 'A')); pin(mp, 'B').set_pin_value('3.14159265')
    sn = fn(ed, 'FBX_Sin', K + 'Sin'); link(pin(mp, 'ReturnValue', True), pin(sn, 'A'))
    hold1 = getv('FBX_Hold1', 'FurinaBoltHold'); pm = fn(ed, 'FBX_Pos', K + 'FMax'); link(pin(hold1, 'FurinaBoltHold', True), pin(pm, 'A')); link(pin(sn, 'ReturnValue', True), pin(pm, 'B'))
    ys = fn(ed, 'FBX_Y', K + 'Multiply_DoubleDouble'); link(pin(pm, 'ReturnValue', True), pin(ys, 'A')); pin(ys, 'B').set_pin_value('%.3f' % -STROKE)
    vec = fn(ed, 'FBX_Vec', K + 'MakeVector', X=0.0, Z=0.0); link(pin(ys, 'ReturnValue', True), pin(vec, 'Y'))
    bolt = getv('FBX_BoltGet', 'FurinaBolt')
    sl = fn(ed, 'FBX_SetLoc', '/Script/Engine.SceneComponent:K2_SetRelativeLocation', bSweep='false', bTeleport='true'); link(pin(bolt, 'FurinaBolt', True), sl.find_self_pin()); link(pin(vec, 'ReturnValue', True), pin(sl, 'NewLocation'))
    # 4) 권총 장착 중이면 숨김
    pistol = N['P2_IsActiveFurinaPistolOn_0f1c5244']; nt = fn(ed, 'FBX_NotPistol', K + 'Not_PreBool'); link(pin(pistol, 'ReturnValue', True), pin(nt, 'A'))
    bolt2 = getv('FBX_BoltGet2', 'FurinaBolt'); sv = fn(ed, 'FBX_SetVis', '/Script/Engine.SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(bolt2, 'FurinaBolt', True), sv.find_self_pin()); link(pin(nt, 'ReturnValue', True), pin(sv, 'bNewVisibility'))
    # 5) 실행 선: FurinaMagUpdate.then -> SetKick -> SetHold -> SetLoc -> SetVis -> (기존 다음)
    ev = N['FMG_Update']; old = list(ev.find_then_pin().list_connected_pins()); ev.find_then_pin().break_pin_links()
    link(ev.find_then_pin(), setk.find_execute_pin()); link(setk.find_then_pin(), seth.find_execute_pin()); link(seth.find_then_pin(), sl.find_execute_pin()); link(sl.find_then_pin(), sv.find_execute_pin())
    for p in old: link(sv.find_then_pin(), p)
    return 'added'
def step_kick():
    ed, N = graph()
    if 'FBX_SetKick1' in N: return 'exists'
    ammo = N['M4_SetFurinaAmmo']
    if 'FBT_SetKick1' in N:    # 변수를 정수로 만들었던 옛 노드: 건너뛰도록 연결을 되돌리고 지운다
        oldk = N['FBT_SetKick1']; after = list(oldk.find_then_pin().list_connected_pins()); ammo.find_then_pin().break_pin_links()
        for p in after: link(ammo.find_then_pin(), p)
        ed.remove_nodes([oldk]); del oldk, after
    old = list(ammo.find_then_pin().list_connected_pins()); assert old, 'no next after M4_SetFurinaAmmo'
    k = ed.add_set_member_variable_node('FurinaBoltKick'); k.rename('FBX_SetKick1'); pin(k, 'FurinaBoltKick').set_pin_value('1.0')
    ammo.find_then_pin().break_pin_links(); link(ammo.find_then_pin(), k.find_execute_pin())
    for p in old: link(k.find_then_pin(), p)
    return ['added', [p.get_owning_node().get_name() for p in old]]
def step_reload():
    ed, N = graph()
    if 'FBT_EmptyBr' in N: return 'exists'
    K = '/Script/Engine.KismetMathLibrary:'
    prog('reload start')
    ammo = ed.add_get_member_variable_node('FurinaAmmo'); ammo.rename('FBT_Ammo2'); le = fn(ed, 'FBT_AmmoLe0b', K + 'LessEqual_IntInt', B=0); link(pin(ammo, 'FurinaAmmo', True), pin(le, 'A'))
    prog('cond1')
    # 타이머 시간: 소총이고 잔탄 0 이면 2.0초
    pistol = N['P2_IsActiveFurinaPistolOn_0f1c5244']; nt = fn(ed, 'FBT_NotPistol2', K + 'Not_PreBool'); link(pin(pistol, 'ReturnValue', True), pin(nt, 'A'))
    an = fn(ed, 'FBT_EmptyCond', K + 'BooleanAND'); link(pin(le, 'ReturnValue', True), pin(an, 'A')); link(pin(nt, 'ReturnValue', True), pin(an, 'B'))
    tm = fn(ed, 'FBT_TimeSel', K + 'SelectFloat', A=2.0); link(pin(an, 'ReturnValue', True), pin(tm, 'bPickA'))
    timer = N['M4_ReloadTimer']; tp = pin(timer, 'Time'); src = list(tp.list_connected_pins()); assert src, 'timer Time not linked'
    tp.break_pin_links(); link(src[0], pin(tm, 'B')); link(pin(tm, 'ReturnValue', True), tp)
    prog('timer relinked')
    # 몽타주 분기 (소총 경로: P2_Branch_59c2bc16.else -> [잔탄 0?] -> 긴급 몽타주 / 기존 몽타주)
    br = ed.add_branch_node(); br.rename('FBT_EmptyBr')
    cond = br.find_condition_pin() if hasattr(br, 'find_condition_pin') else pin(br, 'Condition'); link(pin(le, 'ReturnValue', True), cond)
    prog('branch made')
    play = ed.add_call_function_node('/Script/Engine.AnimInstance:Montage_Play'); play.rename('FBT_EmptyMontage'); prog('play node made')
    pin(play, 'MontageToPlay').set_pin_value('/Game/Furina/FP/Anim/AM_Furina_FP_ReloadEmpty.AM_Furina_FP_ReloadEmpty'); pin(play, 'bStopAllMontages').set_pin_value('true')
    prog('montage default set')
    link(pin(N['K2Node_FP_ReloadAnimInst'], 'ReturnValue', True), pin(play, 'self'))
    gate = N['P2_Branch_59c2bc16']; ep = gate.find_else_pin() if hasattr(gate, 'find_else_pin') else pin(gate, 'else', True)
    old = list(ep.list_connected_pins()); assert old, 'gate else not linked'
    ep.break_pin_links(); link(ep, br.find_execute_pin())
    link(pin(br, 'then', True), play.find_execute_pin()); link(pin(br, 'else', True), N['K2Node_FP_ReloadMontage'].find_execute_pin())
    link(play.find_then_pin(), N['K2Node_FP_ReloadRifle'].find_execute_pin())
    return ['added', [p.get_owning_node().get_name() for p in old]]
funcs = {'comp': step_comp, 'vars': step_vars, 'tick': step_tick, 'kick': step_kick, 'reload': step_reload}
try:
    failed = False
    for s in STEPS:
        pre = set(k for k in graph()[1] if k.startswith('FBT_')) if s in ('tick', 'kick', 'reload') else set()
        try: R['log'].append([s, funcs[s]()])
        except Exception:
            R['log'].append([s, 'ERROR ' + traceback.format_exc()[-900:]]); failed = True
            break
        if s in ('comp', 'vars'): BEL.compile_blueprint(bp)
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['failed'] = failed
    if failed: R['note'] = '실패한 단계의 노드가 메모리에 남아 있다: 저장하지 않았으니 에디터를 다시 시작할 것'
    if not failed and bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BOLT_GRAPH', R.get('status'), json.dumps(R['log'], ensure_ascii=False, default=str)[:400])
for _n in ('bp', 'sub', 'lib', 'funcs', 'ed', 'N'):   # 에디터의 파이썬 전역에 블루프린트/노드 래퍼를 남기면 다음 GC(맵 로드 등)에서 에디터가 죽는다
    globals().pop(_n, None)
import gc; gc.collect()
