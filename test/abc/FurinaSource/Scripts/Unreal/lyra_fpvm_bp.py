"""헤드리스(에디터 세션당 한 번): Kar98k 1인칭 뷰모델(SK_FPVM_Kar98k)을 캐릭터 BP 에 연결.  노드 접두사 VM_
 1) 컴포넌트 FurinaFPVM(SkeletalMesh, 부모 FPCamera, 상대 변환 0 = 카메라 공간으로 만든 메시), 단일 애니 모드, 충돌 없음, 그림자 없음, 처음엔 숨김
 2) 변수: FurinaPrimaryKey(문자열, 무기창이 넣음), FurinaVMOn(불), FurinaVMBusy(실수: 이 게임 시간까지 동작 중), FurinaVMFireLen 1.2 / FurinaVMReloadLen 3.2,
    FurinaVMIdle(불), FurinaVMReloadPlaying(불), FurinaVMAds(실수 0~1), AS 3개(오브젝트 변수)
 3) FurinaMagUpdate(0.033초 타이머, FMG_Update) 맨 앞:
    on = FPCamera 활성 AND 키 == 'kar98k' AND NOT 권총
    on 이 바뀌면: 뷰모델 보이기 = on, 소총(FurinaRifle, 자식 포함) 보이기 = NOT on, on 이면 Idle(반복) 재생
    on 이면: 재장전 중이고 아직 안 틀었으면 Reload 재생(3.2초) / 동작 끝났고 Idle 아니면 Idle 재생 / 정조준 가중치(21/s) 로 상대 변환 = TLerp(0, ADS)
    기존 1인칭 팔 로직: 팔 표시 = 기존 AND NOT on, 본체 팔 숨김 = 기존 OR on
 4) FurinaRifleShot(발사 이벤트) 맨 앞: on 이면 Busy 가 지났을 때만 Fire 재생 + Busy = 지금 + 1.2 후 원래 발사 진행, 아니면 발사 안 함(볼트 조작 중)
 -> Data/lyra_fpvm_bp.json"""
import unreal, json, sys, traceback, time
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; VM = '/Game/Furina/FPVM/Kar98k/'
ADS = json.load(open(D + r'\fpvm_kar98k_ads.json')); TOK = '%x' % (int(time.time()) % 0xFFFFF)
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': [], 'tok': TOK}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    if 'FurinaFPVM' not in handles():
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FPCamera'], new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text('FurinaFPVM')); R['log'].append('added FurinaFPVM')
    c = comp('FurinaFPVM')
    try: c.set_editor_property('skeletal_mesh_asset', unreal.load_asset(VM + 'SK_FPVM_Kar98k'))
    except Exception: c.set_skeletal_mesh_asset(unreal.load_asset(VM + 'SK_FPVM_Kar98k'))
    c.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); c.set_editor_property('relative_rotation', unreal.Rotator(0, 0, 0)); c.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
    c.set_editor_property('visible', False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property('cast_shadow', False)
    c.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    for k, v in (('only_owner_see', True), ('generate_overlap_events', False), ('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)):
        try: c.set_editor_property(k, v)
        except Exception as e: R['log'].append('opt %s: %s' % (k, e))
    names = [str(x) for x in BEL.list_member_variable_names(bp)]
    T = BEL.get_basic_type_by_name
    for v, ty in (('FurinaPrimaryKey', 'string'), ('FurinaVMOn', 'bool'), ('FurinaVMBusy', 'real'), ('FurinaVMFireLen', 'real'), ('FurinaVMReloadLen', 'real'), ('FurinaVMIdle', 'bool'), ('FurinaVMReloadPlaying', 'bool'), ('FurinaVMAds', 'real')):
        if v not in names: BEL.add_member_variable(bp, v, T(ty)); R['log'].append('var ' + v)
    for v in ('FurinaVMAnimIdle', 'FurinaVMAnimFire', 'FurinaVMAnimReload'):
        if v not in names: BEL.add_member_variable(bp, v, BEL.get_object_reference_type(unreal.AnimSequenceBase)); R['log'].append('var ' + v)
    BEL.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    for v, val in (('FurinaVMFireLen', 1.2), ('FurinaVMReloadLen', 3.2), ('FurinaVMAnimIdle', unreal.load_asset(VM + 'AS_FPVM_Kar98k_Idle')), ('FurinaVMAnimFire', unreal.load_asset(VM + 'AS_FPVM_Kar98k_Fire')), ('FurinaVMAnimReload', unreal.load_asset(VM + 'AS_FPVM_Kar98k_Reload'))):
        cdo.set_editor_property(v, val)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    K = '/Script/Engine.KismetMathLibrary:'; E = '/Script/Engine.'
    if any(n.startswith('VM_') for n in N): R['note'] = 'VM_ nodes exist; skipped graph edit'; raise SystemExit
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b):
        assert a is not None and b is not None and a.is_valid() and b.is_valid(), ('link', a, b)
        assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    cnt = [0]
    def nm(t): cnt[0] += 1; return 'VM_%s_%d_%s' % (t, cnt[0], TOK)
    def fn(t, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(nm(t))
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    def getv(var): n = ed.add_get_member_variable_node(var); n.rename(nm('G' + var[-6:])); return pin(n, var, True)
    def setv(var, src=None, const=None):
        n = ed.add_set_member_variable_node(var); n.rename(nm('S' + var[-6:]))
        if src is not None: link(src, pin(n, var))
        if const is not None: pin(n, var).set_pin_value(str(const))
        return n
    def isact(var): f = fn('Act', E + 'ActorComponent:IsActive'); link(getv(var), f.find_self_pin()); return pin(f, 'ReturnValue', True)
    def b_and(a, b): n = fn('And', K + 'BooleanAND'); link(a, pin(n, 'A')); link(b, pin(n, 'B')); return pin(n, 'ReturnValue', True)
    def b_or(a, b): n = fn('Or', K + 'BooleanOR'); link(a, pin(n, 'A')); link(b, pin(n, 'B')); return pin(n, 'ReturnValue', True)
    def b_not(a): n = fn('Not', K + 'Not_PreBool'); link(a, pin(n, 'A')); return pin(n, 'ReturnValue', True)
    def now(): n = fn('Now', E + 'GameplayStatics:GetTimeSeconds'); return pin(n, 'ReturnValue', True)
    def branch(cond): b = ed.add_branch_node(); b.rename(nm('Br')); link(cond, pin(b, 'Condition')); return b
    def play(anim_var, loop):
        n = fn('Play', E + 'SkeletalMeshComponent:PlayAnimation', bLooping='true' if loop else 'false'); link(getv('FurinaFPVM'), n.find_self_pin()); link(getv(anim_var), pin(n, 'NewAnimToPlay')); return n
    def chain(*nodes):
        for a, b in zip(nodes, nodes[1:]): link(a.find_then_pin(), b.find_execute_pin())
        return nodes[0], nodes[-1]
    # ---- on 계산
    ks = fn('KeyEq', '/Script/Engine.KismetStringLibrary:EqualEqual_StrStr', B='kar98k'); link(getv('FurinaPrimaryKey'), pin(ks, 'A'))
    ON = b_and(b_and(isact('FPCamera'), pin(ks, 'ReturnValue', True)), b_not(isact('FurinaPistolOn')))
    # ---- 바뀔 때
    ne = fn('Chg', K + 'NotEqual_BoolBool'); link(ON, pin(ne, 'A')); link(getv('FurinaVMOn'), pin(ne, 'B'))
    bChg = branch(pin(ne, 'ReturnValue', True))
    vv = fn('VisVM', E + 'SceneComponent:SetVisibility', bPropagateToChildren='false'); link(getv('FurinaFPVM'), vv.find_self_pin()); link(ON, pin(vv, 'bNewVisibility'))
    vr = fn('VisRifle', E + 'SceneComponent:SetVisibility', bPropagateToChildren='true'); link(getv('FurinaRifle'), vr.find_self_pin()); link(b_not(ON), pin(vr, 'bNewVisibility'))
    sOn = setv('FurinaVMOn', src=ON); sIdle0 = setv('FurinaVMIdle', const='false'); sRl0 = setv('FurinaVMReloadPlaying', const='false')
    chain(vv, vr, sOn, sIdle0, sRl0); link(bChg.find_then_pin(), vv.find_execute_pin())
    # ---- on 일 때 동작
    bOn = branch(getv('FurinaVMOn')); link(sRl0.find_then_pin(), bOn.find_execute_pin()); link(bChg.find_else_pin(), bOn.find_execute_pin())
    #  재장전 시작
    rlc = b_and(getv('FurinaReloading'), b_not(getv('FurinaVMReloadPlaying'))); bRl = branch(rlc); link(bOn.find_then_pin(), bRl.find_execute_pin())
    pR = play('FurinaVMAnimReload', False); addR = fn('AddR', K + 'Add_DoubleDouble'); link(now(), pin(addR, 'A')); link(getv('FurinaVMReloadLen'), pin(addR, 'B'))
    sBusyR = setv('FurinaVMBusy', src=pin(addR, 'ReturnValue', True)); sRl1 = setv('FurinaVMReloadPlaying', const='true'); sIdR = setv('FurinaVMIdle', const='false')
    chain(pR, sBusyR, sRl1, sIdR); link(bRl.find_then_pin(), pR.find_execute_pin())
    #  재장전 표시 해제(재장전 끝)
    bRlEnd = branch(b_and(getv('FurinaVMReloadPlaying'), b_not(getv('FurinaReloading')))); link(sIdR.find_then_pin(), bRlEnd.find_execute_pin()); link(bRl.find_else_pin(), bRlEnd.find_execute_pin())
    sRl2 = setv('FurinaVMReloadPlaying', const='false'); link(bRlEnd.find_then_pin(), sRl2.find_execute_pin())
    #  동작 끝 -> Idle
    gt = fn('Done', K + 'Greater_DoubleDouble'); link(now(), pin(gt, 'A')); link(getv('FurinaVMBusy'), pin(gt, 'B'))
    bIdle = branch(b_and(pin(gt, 'ReturnValue', True), b_not(getv('FurinaVMIdle')))); link(sRl2.find_then_pin(), bIdle.find_execute_pin()); link(bRlEnd.find_else_pin(), bIdle.find_execute_pin())
    pI = play('FurinaVMAnimIdle', True); sId1 = setv('FurinaVMIdle', const='true'); chain(pI, sId1); link(bIdle.find_then_pin(), pI.find_execute_pin())
    #  정조준 정렬
    sel = fn('AdsT', K + 'SelectFloat', A='1.0', B='0.0'); link(isact('FurinaADS'), pin(sel, 'bPickA'))
    it = fn('AdsI', K + 'FInterpTo', DeltaTime='0.033', InterpSpeed='21.0'); link(getv('FurinaVMAds'), pin(it, 'Current')); link(pin(sel, 'ReturnValue', True), pin(it, 'Target'))
    sAds = setv('FurinaVMAds', src=pin(it, 'ReturnValue', True))
    q = ADS['ue_quat_xyzw']; l = ADS['ue_loc_cm']; rot = unreal.Quat(q[0], q[1], q[2], q[3]).rotator(); R['ads_rot'] = [rot.pitch, rot.yaw, rot.roll]
    tl = fn('AdsL', K + 'TLerp')   # A/B 는 참조 핀이라 MakeTransform 으로 연결해야 함
    mA = fn('AdsA', K + 'MakeTransform', Scale='1.000000,1.000000,1.000000'); mB = fn('AdsB', K + 'MakeTransform', Location='%.6f,%.6f,%.6f' % (l[0], l[1], l[2]), Rotation='%.6f,%.6f,%.6f' % (rot.pitch, rot.yaw, rot.roll), Scale='1.000000,1.000000,1.000000')
    link(pin(mA, 'ReturnValue', True), pin(tl, 'A')); link(pin(mB, 'ReturnValue', True), pin(tl, 'B')); R['adsB_pins'] = [str(pin(mB, 'Location').get_pin_value()), str(pin(mB, 'Rotation').get_pin_value())]
    link(pin(sAds, 'Output_Get', True), pin(tl, 'Alpha'))
    srt = fn('AdsSet', E + 'SceneComponent:K2_SetRelativeTransform'); link(getv('FurinaFPVM'), srt.find_self_pin()); link(pin(tl, 'ReturnValue', True), pin(srt, 'NewTransform'))
    chain(sAds, srt); link(sId1.find_then_pin(), sAds.find_execute_pin()); link(bIdle.find_else_pin(), sAds.find_execute_pin())
    R['tlerp_B'] = str(pin(tl, 'B').get_pin_value())
    ENDS = [bOn.find_else_pin(), srt.find_then_pin()]
    # ---- FMG_Update 맨 앞에 끼우기
    ev = N['FMG_Update']; old = list(ev.find_then_pin().list_connected_pins()); R['fmg_old_next'] = [p.get_owning_node().get_name() for p in old]
    ev.find_then_pin().break_pin_links(); link(ev.find_then_pin(), bChg.find_execute_pin())
    for p in old:
        for o in ENDS: link(o, p)
    # ---- 기존 1인칭 팔: 표시 = 기존 AND NOT on, 본체 팔 숨김 = 기존 OR on
    arms = N['FPA_ArmsOn']; bpin = pin(arms, 'B'); src = list(bpin.list_connected_pins()); bpin.break_pin_links()
    nv = b_not(getv('FurinaVMOn')); a2 = fn('ArmsAnd', K + 'BooleanAND'); link(src[0], pin(a2, 'A')); link(nv, pin(a2, 'B')); link(pin(a2, 'ReturnValue', True), bpin)
    for tag, want_src in (('R', 'FPA_ArmsOn'), ('L', 'FPA_LeftOn')):
        o = b_or(pin(N[want_src], 'ReturnValue', True), getv('FurinaVMOn'))
        for nn, pn in (('FPA_Diff' + tag, 'B'), ('FPA_BrW' + tag, 'Condition')):
            pp = pin(N[nn], pn); pp.break_pin_links(); link(o, pp)
    # ---- 발사 이벤트 앞
    # 발사 이벤트 노드: M4_SetFurinaAmmo 에서 실행 선을 거꾸로 따라가 첫 커스텀 이벤트(이름 속성은 파이썬에서 못 읽음)
    seen = set(); fr = [N['M4_SetFurinaAmmo']]; shot = None
    while fr and shot is None:
        n = fr.pop(0)
        if n.get_name() in seen: continue
        seen.add(n.get_name())
        if n.get_class().get_name() == 'K2Node_CustomEvent': shot = n; break
        ep = n.find_execute_pin()
        if ep is None or not ep.is_valid(): continue
        fr += [q.get_owning_node() for q in ep.list_connected_pins()]
    assert shot is not None, 'FurinaRifleShot 없음'; R['shot_node'] = shot.get_name(); R['shot_path_len'] = len(seen)
    old = list(shot.find_then_pin().list_connected_pins()); R['shot_old_next'] = [p.get_owning_node().get_name() for p in old]
    bF = branch(getv('FurinaVMOn')); gt2 = fn('Ready', K + 'Greater_DoubleDouble'); link(now(), pin(gt2, 'A')); link(getv('FurinaVMBusy'), pin(gt2, 'B'))
    bReady = branch(pin(gt2, 'ReturnValue', True)); link(bF.find_then_pin(), bReady.find_execute_pin())
    pF = play('FurinaVMAnimFire', False); addF = fn('AddF', K + 'Add_DoubleDouble'); link(now(), pin(addF, 'A')); link(getv('FurinaVMFireLen'), pin(addF, 'B'))
    sBusyF = setv('FurinaVMBusy', src=pin(addF, 'ReturnValue', True)); sIdF = setv('FurinaVMIdle', const='false'); chain(pF, sBusyF, sIdF); link(bReady.find_then_pin(), pF.find_execute_pin())
    shot.find_then_pin().break_pin_links(); link(shot.find_then_pin(), bF.find_execute_pin())
    for p in old: link(bF.find_else_pin(), p); link(sIdF.find_then_pin(), p)
    R['added'] = cnt[0]
    del ed, N, sub, lib
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
try: run()
except SystemExit: pass
except Exception: R['error'] = traceback.format_exc()[-1800:]
json.dump(R, open(D + r'\lyra_fpvm_bp.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FPVM_BP', R.get('status'), R.get('error', '')[-400:])
import gc; gc.collect()
