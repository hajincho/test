"""2단계 A: 입력(1/2 키) + 무기 교체(스왑 모션) + 슬라이드 후퇴 애니메이션 이벤트.  p200_graph_lib.py 를 exec 한 뒤 실행."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
SWAP_DZ = -12.0; SWAP_DP = 45.0          # 교체 중 소총 소켓 기준 하강량(cm) / 피치 회전(도) -- PIE 에서 방향 확인 후 조정
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-900:]])
R['cleanup'] = cleanup()
# ---------------- 입력 액션 + IMC
def inputs():
    tools = unreal.AssetToolsHelpers.get_asset_tools(); out = []
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    out.append(['before', [m for m in listing() if m[0] in ('One', 'Two')]])
    for nm, k in (('IA_FurinaWeapon1', 'One'), ('IA_FurinaWeapon2', 'Two')):
        p = '/Game/Furina/Input/' + nm
        ia = unreal.load_asset(p) if EAL.does_asset_exist(p) else tools.create_asset(nm, '/Game/Furina/Input', unreal.InputAction, None)
        ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); ia.set_editor_property('triggers', [])
        EAL.save_loaded_asset(ia, False)
        if (k, nm) not in listing(): imc.map_key(ia, key(k))
    EAL.save_loaded_asset(imc, False)
    out.append(['after', [m for m in listing() if m[0] in ('One', 'Two')]]); return out
step('inputs', inputs)
# ---------------- 애니메이션 틱 이벤트 (슬라이드 + 스왑)
def tick_event():
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    rifle = None
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        if str(lib.get_variable_name(d)) == 'FurinaRifle': rifle = lib.get_associated_object(d)
    loc = rifle.get_editor_property('relative_location'); rot = rifle.get_editor_property('relative_rotation')
    R['rifle_base'] = [loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw]
    ev = ed.add_custom_event_node('FurinaP200Tick'); ev.rename('P2_Ev_Tick')
    # 슬라이드: 목표 = 탄이 있으면 0, 없으면 -2.2 (슬라이드 홀드오픈)
    tgt = selfloat(0.0, -2.2, fn(KML + 'Greater_IntInt', 'Gt').find_result_pin() if False else None) if False else None
    gt = fn(KML + 'Greater_IntInt', 'AmmoGt'); link(getvar('FurinaAmmo'), gt.find_input_pin('A')); ival(gt.find_input_pin('B'), 0)
    tgt = selfloat(0.0, -2.2, gt.find_result_pin())
    fi = fn(KML + 'FInterpTo', 'SlideInterp'); link(getvar('FurinaSlideCur'), fi.find_input_pin('Current')); link(tgt, fi.find_input_pin('Target'))
    fval(fi.find_input_pin('DeltaTime'), 0.008); fval(fi.find_input_pin('InterpSpeed'), 32.0)
    s1 = setvar('FurinaSlideCur'); link(fi.find_result_pin(), s1.find_input_pin('FurinaSlideCur'))
    sl = fn('/Script/Engine.SceneComponent:K2_SetRelativeLocation', 'SlideLoc'); link(comp_get('FurinaPistolSlide'), sl.find_self_pin()); link(mkvec(fi.find_result_pin(), 0.0, 0.0), sl.find_input_pin('NewLocation'))
    # 스왑: SwapCur -> 소총 소켓 상대 위치/회전 오프셋
    fs = fn(KML + 'FInterpTo', 'SwapInterp'); link(getvar('FurinaSwapCur'), fs.find_input_pin('Current')); link(getvar('FurinaSwapTarget'), fs.find_input_pin('Target'))
    fval(fs.find_input_pin('DeltaTime'), 0.008); fval(fs.find_input_pin('InterpSpeed'), 8.0)
    s2 = setvar('FurinaSwapCur'); link(fs.find_result_pin(), s2.find_input_pin('FurinaSwapCur'))
    a = fs.find_result_pin()
    bx, by, bz, br, bpi, byw = R['rifle_base']
    rl = fn('/Script/Engine.SceneComponent:K2_SetRelativeLocation', 'RifleLoc'); link(comp_get('FurinaRifle'), rl.find_self_pin())
    link(mkvec(bx, by, addf(lit(bz), mulf(a, lit(SWAP_DZ)))), rl.find_input_pin('NewLocation'))
    rr = fn('/Script/Engine.SceneComponent:K2_SetRelativeRotation', 'RifleRot'); link(comp_get('FurinaRifle'), rr.find_self_pin())
    link(mkrot(br, addf(lit(bpi), mulf(fs.find_result_pin(), lit(SWAP_DP))), byw), rr.find_input_pin('NewRotation'))
    link(ev.find_then_pin(), s1.find_execute_pin()); chain(s1, sl, s2, rl, rr)
    return 'tick ok'
step('tick_event', tick_event)
# ---------------- 사격 FX: 슬라이드 킥 (타이머로 호출)
def fx_event():
    ev = ed.add_custom_event_node('FurinaPistolFx'); ev.rename('P2_Ev_Fx')
    s = setvar('FurinaSlideCur'); fval(s.find_input_pin('FurinaSlideCur'), -2.7); link(ev.find_then_pin(), s.find_execute_pin()); return 'fx ok'
step('fx_event', fx_event)
# ---------------- 교체 로직
def swap_logic():
    s0 = set_active('FurinaSwapping', True); s1 = setvar('FurinaSwapTarget'); fval(s1.find_input_pin('FurinaSwapTarget'), 1.0); s2 = timer('FurinaSwapMid', 0.2)
    chain(s0, s1, s2)
    def cond(want_pistol_on):
        base = band(bnot(is_active('FurinaSwapping')), bnot(getvar('FurinaReloading')))
        po = is_active('FurinaPistolOn')
        return band(base, po if want_pistol_on else bnot(po))
    # 2 키 -> 권총 (현재 권총 아님), 1 키 -> 소총 (현재 권총)
    for ianame, want in (('IA_FurinaWeapon2', False), ('IA_FurinaWeapon1', True)):
        evn = ed.create_node_from_name('Input|EnhancedActionEvents|' + ianame, unreal.Vector2D(-2400, 7000 if not want else 7300), []); assert evn, ianame
        evn.rename('P2_IA_' + ianame)
        b = branch(cond(want)); link(evn.find_output_pin('Started'), b.find_execute_pin()); link(b.find_then_pin(), s0.find_execute_pin())
    # 중간 시점: 무기 모델 교체 + 탄약 교환
    ev = ed.add_custom_event_node('FurinaSwapMid'); ev.rename('P2_Ev_SwapMid')
    br = branch(is_active('FurinaPistolOn')); link(ev.find_then_pin(), br.find_execute_pin())
    def vis(compname, on, prefix):
        n = fn('/Script/Engine.SceneComponent:SetVisibility', prefix); link(comp_get(compname), n.find_self_pin())
        n.find_input_pin('bNewVisibility').set_pin_value('true' if on else 'false'); n.find_input_pin('bPropagateToChildren').set_pin_value('false'); return n
    def mesh(path):
        n = fn('/Script/Engine.StaticMeshComponent:SetStaticMesh', 'SetMagMesh'); link(comp_get('FurinaMag'), n.find_self_pin()); n.find_input_pin('NewMesh').set_pin_value(path); return n
    to_rifle = [set_active('FurinaPistolOn', False), vis('FurinaRifle', True, 'VisRifle'), vis('FurinaPistolFrame', False, 'VisFrame'), vis('FurinaPistolSlide', False, 'VisSlide'), mesh('/Game/Furina/M4/SM_M4Mag.SM_M4Mag')]
    to_pistol = [set_active('FurinaPistolOn', True), vis('FurinaRifle', False, 'VisRifle'), vis('FurinaPistolFrame', True, 'VisFrame'), vis('FurinaPistolSlide', True, 'VisSlide'), mesh('None')]
    chain(*to_rifle); chain(*to_pistol)
    link(br.find_then_pin(), to_rifle[0].find_execute_pin()); link(br.find_else_pin(), to_pistol[0].find_execute_pin())
    def sv(name, src_pin):
        n = setvar(name); link(src_pin, n.find_input_pin(name)); return n
    c = [sv('FurinaSwapTmp', getvar('FurinaAmmo')), sv('FurinaAmmo', getvar('FurinaAmmoStash')), sv('FurinaAmmoStash', getvar('FurinaSwapTmp')),
         sv('FurinaSwapTmp', getvar('FurinaReserve')), sv('FurinaReserve', getvar('FurinaReserveStash')), sv('FurinaReserveStash', getvar('FurinaSwapTmp'))]
    c7 = setvar('FurinaSwapTarget'); fval(c7.find_input_pin('FurinaSwapTarget'), 0.0); c8 = timer('FurinaSwapEnd', 0.22)
    chain(*c, c7, c8)
    link(to_rifle[-1].find_then_pin(), c[0].find_execute_pin()); link(to_pistol[-1].find_then_pin(), c[0].find_execute_pin())
    ev2 = ed.add_custom_event_node('FurinaSwapEnd'); ev2.rename('P2_Ev_SwapEnd'); e1 = set_active('FurinaSwapping', False); link(ev2.find_then_pin(), e1.find_execute_pin())
    return 'swap ok'
step('swap_logic', swap_logic)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
errs = [str(x.get_name()) for x in ed.list_nodes_with_errors()] if hasattr(ed, 'list_nodes_with_errors') else []
R['nodes_with_errors'] = errs[:20]
print('P200_GRAPH_A', json.dumps(R, default=str, ensure_ascii=False)[:3500])
