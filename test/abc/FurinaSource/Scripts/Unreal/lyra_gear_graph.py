"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 이 스크립트만 한 번): 3인칭 등 매기/홀스터 권총 동작 로직을 ThirdPersonCharacter_BP 에 넣는다.
 1) 컴포넌트 상대 위치/회전 = Data/gear_place_v1.json (뼈 소켓 기준; PIE 뼈 변환으로 계산)
 2) FurinaMagUpdate(0.016초 타이머) 맨 앞에:
    - 1회: FurinaSlingM4 를 FurinaMesh 소켓 Spine 에, FurinaHolsterFrame 을 소켓 Hips 에 AttachToComponent(KeepRelative)  (bool 변수 FurinaGearAttached)
    - 매 틱: FurinaSlingM4.SetVisibility( PistolOn 활성 AND NOT FPWanted 활성 ),  FurinaHolsterFrame.SetVisibility( NOT PistolOn AND NOT FPWanted, 자식 포함 )
 노드: FGR_*   -> Data/lyra_gear_graph.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
G = json.load(open(D + r'\gear_place_v1.json'))
BEL = unreal.BlueprintEditorLibrary; CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(n): return lib.get_associated_object(lib.get_data(hs[n]))
    for nm, key in (('FurinaSlingM4', 'sling'), ('FurinaHolsterFrame', 'holster')):
        c = comp(nm); q = G[key]['q']; rot = unreal.Quat(q[0], q[1], q[2], q[3]).rotator(); l = G[key]['loc']
        c.set_editor_property('relative_location', unreal.Vector(l[0], l[1], l[2])); c.set_editor_property('relative_rotation', rot); R['log'].append([nm, l, [rot.pitch, rot.yaw, rot.roll]])
    existing = [str(x) for x in BEL.list_member_variable_names(bp)]
    if 'FurinaGearAttached' not in existing: R['var'] = BEL.add_member_variable(bp, 'FurinaGearAttached', BEL.get_basic_type_by_name('boolean'))
    BEL.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    assert 'FMG_Update' in N
    Kc = '/Script/Engine.KismetMathLibrary:'
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
    if 'FGR_Br' in N: R['note'] = 'exists'
    else:
        att = getv('FGR_AttGet', 'FurinaGearAttached'); nt = fn('FGR_NotAtt', Kc + 'Not_PreBool'); link(pin(att, 'FurinaGearAttached', True), pin(nt, 'A'))
        br = ed.add_branch_node(); br.rename('FGR_Br'); link(pin(nt, 'ReturnValue', True), pin(br, 'Condition'))
        mesh = getv('FGR_MeshGet', 'FurinaMesh'); sl = getv('FGR_SlingGet', 'FurinaSlingM4'); hf = getv('FGR_HolGet', 'FurinaHolsterFrame')
        a1 = fn('FGR_Att1', '/Script/Engine.SceneComponent:K2_AttachToComponent', SocketName='Spine', LocationRule='KeepRelative', RotationRule='KeepRelative', ScaleRule='KeepRelative', bWeldSimulatedBodies='false')
        link(pin(sl, 'FurinaSlingM4', True), a1.find_self_pin()); link(pin(mesh, 'FurinaMesh', True), pin(a1, 'Parent'))
        a2 = fn('FGR_Att2', '/Script/Engine.SceneComponent:K2_AttachToComponent', SocketName='Hips', LocationRule='KeepRelative', RotationRule='KeepRelative', ScaleRule='KeepRelative', bWeldSimulatedBodies='false')
        link(pin(hf, 'FurinaHolsterFrame', True), a2.find_self_pin()); link(pin(mesh, 'FurinaMesh', True), pin(a2, 'Parent'))
        sv = ed.add_set_member_variable_node('FurinaGearAttached'); sv.rename('FGR_SetAtt'); pin(sv, 'FurinaGearAttached').set_pin_value('true')
        link(br.find_then_pin(), a1.find_execute_pin()); link(a1.find_then_pin(), a2.find_execute_pin()); link(a2.find_then_pin(), sv.find_execute_pin())
        # 가시성
        def isact(name, var):
            g = getv(name + 'G', var); f = fn(name + 'A', '/Script/Engine.ActorComponent:IsActive'); link(pin(g, var, True), f.find_self_pin()); return f
        po = isact('FGR_Po', 'FurinaPistolOn'); fp = isact('FGR_Fp', 'FurinaFPWanted')
        nfp = fn('FGR_NotFp', Kc + 'Not_PreBool'); link(pin(fp, 'ReturnValue', True), pin(nfp, 'A'))
        npo = fn('FGR_NotPo', Kc + 'Not_PreBool'); link(pin(po, 'ReturnValue', True), pin(npo, 'A'))
        slv = fn('FGR_SlingVisCond', Kc + 'BooleanAND'); link(pin(po, 'ReturnValue', True), pin(slv, 'A')); link(pin(nfp, 'ReturnValue', True), pin(slv, 'B'))
        hov = fn('FGR_HolVisCond', Kc + 'BooleanAND'); link(pin(npo, 'ReturnValue', True), pin(hov, 'A')); link(pin(nfp, 'ReturnValue', True), pin(hov, 'B'))
        sl2 = getv('FGR_SlingGet2', 'FurinaSlingM4'); hf2 = getv('FGR_HolGet2', 'FurinaHolsterFrame')
        v1 = fn('FGR_SlingVis', '/Script/Engine.SceneComponent:SetVisibility', bPropagateToChildren='false'); link(pin(sl2, 'FurinaSlingM4', True), v1.find_self_pin()); link(pin(slv, 'ReturnValue', True), pin(v1, 'bNewVisibility'))
        v2 = fn('FGR_HolVis', '/Script/Engine.SceneComponent:SetVisibility', bPropagateToChildren='true'); link(pin(hf2, 'FurinaHolsterFrame', True), v2.find_self_pin()); link(pin(hov, 'ReturnValue', True), pin(v2, 'bNewVisibility'))
        link(sv.find_then_pin(), v1.find_execute_pin()); link(br.find_else_pin(), v1.find_execute_pin()); link(v1.find_then_pin(), v2.find_execute_pin())
        ev = N['FMG_Update']; old = list(ev.find_then_pin().list_connected_pins()); ev.find_then_pin().break_pin_links()
        link(ev.find_then_pin(), br.find_execute_pin())
        for p in old: link(v2.find_then_pin(), p)
        R['added'] = True
    del ed, N, sub, lib
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(D + r'\lyra_gear_graph.json', 'w'), indent=1, default=str); print('LYRA_GEAR_GRAPH', R.get('status'), R.get('error', ''))
import gc; gc.collect()
