"""헤드리스(commandlet, 에디터 세션당 한 번): 1인칭 전용 팔(소총과 한몸)을 ThirdPersonCharacter_BP 에 연결.  인자: <굽기 태그>
 1) 컴포넌트 FurinaFPArmL / FurinaFPArmR (StaticMesh SM_FurinaFPArmL/R, 부모 FurinaRifle, 상대 변환 0 = 소총 로컬로 구운 메시), 충돌 없음, 처음엔 숨김.
 2) FurinaMagUpdate(0.033초 타이머) 맨 앞:
    ArmsOn = FPCamera 활성 AND NOT 권총(FurinaPistolOn)
    재장전 동안 왼팔은 본체(FurinaMesh) 팔로 교체(왼손이 탄창으로 감):  LHold = 재장전 중 0.8, 아니면 0.033씩 감소
    LeftOn = ArmsOn AND NOT 재장전 AND (LHold<=0 OR 본체 왼손목이 구운 위치(소총 로컬)에서 0.5cm 이내)
    FurinaFPArmR 보이기 = ArmsOn, FurinaFPArmL 보이기 = LeftOn
    본체 'Right-arm' 숨김 = ArmsOn, 'Left-arm' 숨김 = LeftOn  (상태가 바뀔 때만 Hide/UnHide 호출)
 이미 있으면 상수(구운 왼손목 위치)만 갱신.   노드: FPA_*   -> Data/lyra_fp_arms_bp.json"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; TAG = ARGS[0] if ARGS else 'a1'
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BK = json.load(open(D + r'\fp_arms_bake_%s.json' % TAG)); LW = BK['wrist_rifle_local']['Left-wrist']
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'tag': TAG, 'lw': LW, 'log': []}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    for side in ('L', 'R'):
        nm = 'FurinaFPArm' + side
        if nm not in handles():
            h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaRifle'], new_class=unreal.StaticMeshComponent, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text(nm)); R['log'].append('added ' + nm)
        c = comp(nm)
        c.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/FPArms/SM_FurinaFPArm' + side))
        c.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); c.set_editor_property('relative_rotation', unreal.Rotator(0, 0, 0)); c.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
        c.set_editor_property('visible', False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('cast_shadow', True); c.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)
        try: c.set_editor_property('generate_overlap_events', False)
        except Exception: pass
    existing = [str(x) for x in BEL.list_member_variable_names(bp)]
    if 'FurinaFPArmLHold' not in existing: R['var'] = bool(BEL.add_member_variable(bp, 'FurinaFPArmLHold', BEL.get_basic_type_by_name('real')))
    BEL.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    K = '/Script/Engine.KismetMathLibrary:'; E = '/Script/Engine.'
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name); return p
    def link(a, b):
        assert a is not None and b is not None and a.is_valid() and b.is_valid(), ('link', a, b)
        assert CONN(a, b), ('link', a.get_owning_node().get_name(), a.get_pin_name(), '->', b.get_owning_node().get_name(), b.get_pin_name())
    def fn(name, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        for k, v in vals.items(): pin(n, k).set_pin_value(str(v))
        return n
    def getv(name, var): n = ed.add_get_member_variable_node(var); n.rename(name); return n
    if 'FPA_LWRef' in N:
        for ax, v in zip('XYZ', LW): pin(N['FPA_LWRef'], ax).set_pin_value('%.4f' % v)
        R['note'] = 'exists: constants updated'
    else:
        def isact(name, var):
            g = getv(name + 'G', var); f = fn(name + 'A', E + 'ActorComponent:IsActive'); link(pin(g, var, True), f.find_self_pin()); return pin(f, 'ReturnValue', True)
        fp = isact('FPA_Fp', 'FPCamera'); po = isact('FPA_Po', 'FurinaPistolOn')
        npo = fn('FPA_NotPo', K + 'Not_PreBool'); link(po, pin(npo, 'A'))
        arms = fn('FPA_ArmsOn', K + 'BooleanAND'); link(fp, pin(arms, 'A')); link(pin(npo, 'ReturnValue', True), pin(arms, 'B')); ARMS = pin(arms, 'ReturnValue', True)
        rl = getv('FPA_Rl', 'FurinaReloading'); RL = pin(rl, 'FurinaReloading', True)
        # LHold 갱신
        hg = getv('FPA_HoldG', 'FurinaFPArmLHold'); dec = fn('FPA_HoldDec', K + 'Subtract_DoubleDouble', B=0.033); link(pin(hg, 'FurinaFPArmLHold', True), pin(dec, 'A'))
        mx = fn('FPA_HoldMax0', K + 'FMax', B=0.0); link(pin(dec, 'ReturnValue', True), pin(mx, 'A'))
        sel = fn('FPA_HoldSel', K + 'SelectFloat', A=0.8); link(pin(mx, 'ReturnValue', True), pin(sel, 'B')); link(RL, pin(sel, 'bPickA'))
        sh = ed.add_set_member_variable_node('FurinaFPArmLHold'); sh.rename('FPA_HoldSet'); link(pin(sel, 'ReturnValue', True), pin(sh, 'FurinaFPArmLHold'))
        # 본체 왼손목 - 구운 위치 거리 (소총 로컬)
        mesh = getv('FPA_Mesh', 'FurinaMesh'); MESH = pin(mesh, 'FurinaMesh', True)
        sl = fn('FPA_LWSock', E + 'SceneComponent:GetSocketLocation', InSocketName='Left-wrist'); link(MESH, sl.find_self_pin())
        rf = getv('FPA_Rifle', 'FurinaRifle'); tw = fn('FPA_RifleTf', E + 'SceneComponent:K2_GetComponentToWorld'); link(pin(rf, 'FurinaRifle', True), tw.find_self_pin())
        inv = fn('FPA_LWLocal', K + 'InverseTransformLocation'); link(pin(tw, 'ReturnValue', True), pin(inv, 'T')); link(pin(sl, 'ReturnValue', True), pin(inv, 'Location'))
        ref = fn('FPA_LWRef', K + 'MakeVector', X='%.4f' % LW[0], Y='%.4f' % LW[1], Z='%.4f' % LW[2])
        dist = fn('FPA_LWDist', K + 'Vector_Distance'); link(pin(inv, 'ReturnValue', True), pin(dist, 'V1')); link(pin(ref, 'ReturnValue', True), pin(dist, 'V2'))
        near = fn('FPA_Near', K + 'Less_DoubleDouble', B=0.5); link(pin(dist, 'ReturnValue', True), pin(near, 'A'))
        hg2 = getv('FPA_HoldG2', 'FurinaFPArmLHold'); le = fn('FPA_HoldDone', K + 'LessEqual_DoubleDouble', B=0.0); link(pin(hg2, 'FurinaFPArmLHold', True), pin(le, 'A'))
        ok = fn('FPA_LOk', K + 'BooleanOR'); link(pin(le, 'ReturnValue', True), pin(ok, 'A')); link(pin(near, 'ReturnValue', True), pin(ok, 'B'))
        nrl = fn('FPA_NotRl', K + 'Not_PreBool'); link(RL, pin(nrl, 'A'))
        a1 = fn('FPA_LA1', K + 'BooleanAND'); link(pin(nrl, 'ReturnValue', True), pin(a1, 'A')); link(pin(ok, 'ReturnValue', True), pin(a1, 'B'))
        lo = fn('FPA_LeftOn', K + 'BooleanAND'); link(ARMS, pin(lo, 'A')); link(pin(a1, 'ReturnValue', True), pin(lo, 'B')); LEFT = pin(lo, 'ReturnValue', True)
        # 보이기
        gr = getv('FPA_ArmRG', 'FurinaFPArmR'); vr = fn('FPA_VisR', E + 'SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(gr, 'FurinaFPArmR', True), vr.find_self_pin()); link(ARMS, pin(vr, 'bNewVisibility'))
        gl = getv('FPA_ArmLG', 'FurinaFPArmL'); vl = fn('FPA_VisL', E + 'SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(gl, 'FurinaFPArmL', True), vl.find_self_pin()); link(LEFT, pin(vl, 'bNewVisibility'))
        link(sh.find_then_pin(), vr.find_execute_pin()); link(vr.find_then_pin(), vl.find_execute_pin())
        # 본체 팔 숨김(바뀔 때만)
        def bone_block(tag, bone, want, prev_outs):
            hid = fn('FPA_Hid' + tag, E + 'SkinnedMeshComponent:IsBoneHiddenByName', BoneName=bone); link(MESH, hid.find_self_pin())
            ne = fn('FPA_Diff' + tag, K + 'NotEqual_BoolBool'); link(pin(hid, 'ReturnValue', True), pin(ne, 'A')); link(want, pin(ne, 'B'))
            b1 = ed.add_branch_node(); b1.rename('FPA_Br' + tag); link(pin(ne, 'ReturnValue', True), pin(b1, 'Condition'))
            b2 = ed.add_branch_node(); b2.rename('FPA_BrW' + tag); link(want, pin(b2, 'Condition'))
            hd = fn('FPA_Hide' + tag, E + 'SkinnedMeshComponent:HideBoneByName', BoneName=bone, PhysBodyOption='PBO_None'); link(MESH, hd.find_self_pin())
            uh = fn('FPA_Unhide' + tag, E + 'SkinnedMeshComponent:UnHideBoneByName', BoneName=bone); link(MESH, uh.find_self_pin())
            for o in prev_outs: link(o, b1.find_execute_pin())
            link(b1.find_then_pin(), b2.find_execute_pin()); link(b2.find_then_pin(), hd.find_execute_pin()); link(b2.find_else_pin(), uh.find_execute_pin())
            return [b1.find_else_pin(), hd.find_then_pin(), uh.find_then_pin()]
        outs = bone_block('R', 'Right-arm', ARMS, [vl.find_then_pin()])
        outs = bone_block('L', 'Left-arm', LEFT, outs)
        ev = N['FMG_Update']; old = list(ev.find_then_pin().list_connected_pins()); R['old_next'] = [p.get_owning_node().get_name() for p in old]
        ev.find_then_pin().break_pin_links(); link(ev.find_then_pin(), sh.find_execute_pin())
        for p in old:
            for o in outs: link(o, p)
        R['added'] = True
    del ed, N, sub, lib
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\lyra_fp_arms_bp.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_ARMS_BP', R.get('status'), R.get('error', ''))
import gc; gc.collect()
