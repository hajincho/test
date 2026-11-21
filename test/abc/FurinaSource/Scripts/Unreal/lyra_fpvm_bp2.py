"""헤드리스(에디터 세션당 한 번): 1인칭 뷰모델을 무기 키별로 전환(kar98k, g43). lyra_fpvm_bp.py 다음에 실행. 노드 접두사 VW_
 FMG_Update 맨 앞: 키(FurinaPrimaryKey) 가 지난번(FurinaVMLastKey) 과 다르면
   kar98k / g43 이면: 메시(SetSkeletalMeshAsset), 현재 애니 3개, 사격 간격(FireLen), 재장전 길이, 정조준 위치/회전 설정, Valid=참, Idle=거짓(새 메시로 Idle 다시)
   그 밖: Valid=거짓
 기존 'on' 계산의 키=='kar98k' 비교를 FurinaVMValid 로 바꾸고, 정조준 MakeTransform(VM_AdsB_*) 을 변수 FurinaVMAdsLoc/Rot 로 연결.
 무기 값: Data/fpvm_<무기>_ads.json, 애니 /Game/Furina/FPVM/<Key>/AS_FPVM_<Key>_*  -> Data/lyra_fpvm_bp2.json"""
import unreal, json, traceback, time
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; TOK = '%x' % (int(time.time()) % 0xFFFFF)
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
# 키, 에셋 폴더 이름, 사격 간격(초: 볼트액션 1.2 / 반자동 0.25), 재장전 애니 길이
W = [('kar98k', 'Kar98k', 1.2, 3.2), ('g43', 'G43', 0.25, 5.9)]
R = {'tok': TOK, 'log': []}
def run():
    bp = unreal.load_asset(PAWN); names = [str(x) for x in BEL.list_member_variable_names(bp)]; T = BEL.get_basic_type_by_name
    newv = [('FurinaVMValid', T('bool')), ('FurinaVMLastKey', T('string'))]
    for k, f, _, _ in W:
        newv += [('FurinaVMMesh_' + k, BEL.get_object_reference_type(unreal.SkeletalMesh))] + [('FurinaVM%s_%s' % (a, k), BEL.get_object_reference_type(unreal.AnimSequenceBase)) for a in ('Idle', 'Fire', 'Reload')]
    for v, ty in newv:
        if v not in names: BEL.add_member_variable(bp, v, ty); R['log'].append('var ' + v)
    for v, st in (('FurinaVMAdsLoc', 'Vector'), ('FurinaVMAdsRot', 'Rotator')):
        if v not in names:
            ok = BEL.add_member_variable(bp, v, BEL.get_struct_type(unreal.Vector.static_struct() if st == 'Vector' else unreal.Rotator.static_struct())); R['log'].append('var %s %s' % (v, ok))
    BEL.compile_blueprint(bp); cdo = unreal.get_default_object(bp.generated_class())
    for k, f, _, _ in W:
        base = '/Game/Furina/FPVM/%s/' % f
        cdo.set_editor_property('FurinaVMMesh_' + k, unreal.load_asset(base + 'SK_FPVM_' + f))
        for a in ('Idle', 'Fire', 'Reload'): cdo.set_editor_property('FurinaVM%s_%s' % (a, k), unreal.load_asset(base + 'AS_FPVM_%s_%s' % (f, a)))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    if any(n.startswith('VW_') for n in N): R['note'] = 'VW_ nodes exist; skipped'; raise SystemExit
    K = '/Script/Engine.KismetMathLibrary:'; E = '/Script/Engine.'; SL = '/Script/Engine.KismetStringLibrary:'
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), ('pin', n.get_name(), name, [str(x.get_pin_name()) for x in n.list_all_pins()]); return p
    def link(a, b): assert CONN(a, b), ('link', a.get_owning_node().get_name(), str(a.get_pin_name()), '->', b.get_owning_node().get_name(), str(b.get_pin_name()))
    cnt = [0]
    def nm(t): cnt[0] += 1; return 'VW_%s_%d_%s' % (t, cnt[0], TOK)
    def fn(t, path, **vals):
        n = ed.add_call_function_node(path); assert n, path; n.rename(nm(t))
        for k_, v in vals.items(): pin(n, k_).set_pin_value(str(v))
        return n
    def getv(var): n = ed.add_get_member_variable_node(var); n.rename(nm('G')); return pin(n, var, True)
    def setv(var, src=None, const=None):
        n = ed.add_set_member_variable_node(var); n.rename(nm('S'))
        if src is not None: link(src, pin(n, var))
        if const is not None: pin(n, var).set_pin_value(str(const))
        return n
    def branch(cond): b = ed.add_branch_node(); b.rename(nm('Br')); link(cond, pin(b, 'Condition')); return b
    def chain(*ns):
        for a, b in zip(ns, ns[1:]): link(a.find_then_pin(), b.find_execute_pin())
    # 키 바뀜
    ne = fn('KeyNe', SL + 'NotEqual_StrStr'); link(getv('FurinaPrimaryKey'), pin(ne, 'A')); link(getv('FurinaVMLastKey'), pin(ne, 'B'))
    bCh = branch(pin(ne, 'ReturnValue', True)); sLast = setv('FurinaVMLastKey', src=getv('FurinaPrimaryKey')); sId = setv('FurinaVMIdle', const='false'); chain(sLast, sId); link(bCh.find_then_pin(), sLast.find_execute_pin())
    prev_false = sId.find_then_pin(); ends = [bCh.find_else_pin()]
    for k, f, fire_len, rl_len in W:
        A = json.load(open(D + r'\fpvm_%s_ads.json' % k)); q = A['ue_quat_xyzw']; l = A['ue_loc_cm']; rot = unreal.Quat(q[0], q[1], q[2], q[3]).rotator()
        eq = fn('Is_' + k, SL + 'EqualEqual_StrStr', B=k); link(getv('FurinaPrimaryKey'), pin(eq, 'A')); b = branch(pin(eq, 'ReturnValue', True)); link(prev_false, b.find_execute_pin())
        sm = fn('Mesh_' + k, E + 'SkeletalMeshComponent:SetSkeletalMeshAsset'); link(getv('FurinaFPVM'), sm.find_self_pin()); link(getv('FurinaVMMesh_' + k), pin(sm, 'NewMesh'))
        s1 = setv('FurinaVMAnimIdle', src=getv('FurinaVMIdle_' + k)); s2 = setv('FurinaVMAnimFire', src=getv('FurinaVMFire_' + k)); s3 = setv('FurinaVMAnimReload', src=getv('FurinaVMReload_' + k))
        s4 = setv('FurinaVMFireLen', const='%.3f' % fire_len); s5 = setv('FurinaVMReloadLen', const='%.3f' % rl_len)
        s6 = setv('FurinaVMAdsLoc', const='%.6f,%.6f,%.6f' % (l[0], l[1], l[2])); s7 = setv('FurinaVMAdsRot', const='%.6f,%.6f,%.6f' % (rot.pitch, rot.yaw, rot.roll)); s8 = setv('FurinaVMValid', const='true')
        chain(sm, s1, s2, s3, s4, s5, s6, s7, s8); link(b.find_then_pin(), sm.find_execute_pin()); ends.append(s8.find_then_pin()); prev_false = b.find_else_pin()
        R.setdefault('ads', {})[k] = [str(pin(s6, 'FurinaVMAdsLoc').get_pin_value()), str(pin(s7, 'FurinaVMAdsRot').get_pin_value())]
    sInv = setv('FurinaVMValid', const='false'); link(prev_false, sInv.find_execute_pin()); ends.append(sInv.find_then_pin())
    # FMG_Update 맨 앞에 끼우기
    ev = N['FMG_Update']; old = list(ev.find_then_pin().list_connected_pins()); R['fmg_old_next'] = [p.get_owning_node().get_name() for p in old]
    ev.find_then_pin().break_pin_links(); link(ev.find_then_pin(), bCh.find_execute_pin())
    for p in old:
        for o in ends: link(o, p)
    # 'on' 의 키 비교 -> Valid
    keq = [n for nm_, n in N.items() if nm_.startswith('VM_KeyEq_')]; assert keq, 'VM_KeyEq 없음'
    rv = pin(keq[0], 'ReturnValue', True); tgt = list(rv.list_connected_pins()); R['keyeq_to'] = [p.get_owning_node().get_name() + '.' + str(p.get_pin_name()) for p in tgt]
    for p in tgt: p.break_pin_links(); link(getv('FurinaVMValid'), p)
    # 정조준 B 변환 -> 변수
    adsb = [n for nm_, n in N.items() if nm_.startswith('VM_AdsB_')]; assert adsb, 'VM_AdsB 없음'
    link(getv('FurinaVMAdsLoc'), pin(adsb[0], 'Location')); link(getv('FurinaVMAdsRot'), pin(adsb[0], 'Rotation'))
    R['added'] = cnt[0]
    del ed, N
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
try: run()
except SystemExit: pass
except Exception: R['error'] = traceback.format_exc()[-1800:]
json.dump(R, open(D + r'\lyra_fpvm_bp2.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FPVM_BP2', R.get('status'), R.get('error', '')[-300:])
import gc; gc.collect()
