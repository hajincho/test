"""ABP_Furina: 3인칭 + 권총 장착 시 이동 포즈를 Lyra 권총 블렌드스페이스로 전환.
 TwoWayBlend_0(소총 서있기/앉기) 와 새 TwoWayBlend(권총 서있기/앉기)를 Alpha=ToFloat(P220_AndTP) 로 섞어서, 기존 TwoWayBlend_0.Pose 를 쓰던 두 곳에 연결.
 백업: FurinaSource/Backup_before_p200/ABP_Furina_with_cr_alpha.uasset   저장은 컴파일 직후."""
import unreal, json, uuid, traceback
PL = unreal.BlueprintGraphPinLibrary; BEL = unreal.BlueprintEditorLibrary; EAL = unreal.EditorAssetLibrary
R = {}
abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph')
def node(n): return next((x for x in ed.list_all_nodes() if x.get_name() == n), None)
def link(a, b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(), 'pin'
    assert PL.try_create_connection(a, b), 'link %s.%s -> %s.%s' % (a.get_owning_node().get_name(), a.get_pin_name(), b.get_owning_node().get_name(), b.get_pin_name())
def uniq(p): return 'P220L_%s_%s' % (p, uuid.uuid4().hex[:6])
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    assert not any(n.get_name().startswith('P220L_') for n in ed.list_all_nodes()), 'already applied'
    tw0 = node('AnimGraphNode_TwoWayBlend_0'); andtp = next(n for n in ed.list_all_nodes() if n.get_name().startswith('P220_AndTP'))
    def mk(path, pos, prefix):
        n = ed.create_node_from_name(path, unreal.Vector2D(*pos), []); assert n, path; n.rename(uniq(prefix)); return n
    ps = mk("애니메이션|블렌드스페이스|블렌드스페이스플레이어'BS_Furina_PistolStanding'", (-2200, 3000), 'PistolStand')
    pc = mk("애니메이션|블렌드스페이스|블렌드스페이스플레이어'BS_Furina_PistolCrouching'", (-2200, 3300), 'PistolCrouch')
    link(node('K2Node_VariableGet_0').find_output_pin('TFPDirection'), ps.find_input_pin('X')); link(node('K2Node_VariableGet_1').find_output_pin('TFPSpeed'), ps.find_input_pin('Y'))
    link(node('K2Node_VariableGet_2').find_output_pin('TFPDirection'), pc.find_input_pin('X')); link(node('K2Node_VariableGet_3').find_output_pin('TFPSpeed'), pc.find_input_pin('Y'))
    tm = mk('애니메이션|블렌드|양방향블렌드', (-1900, 3150), 'PistolMove')
    link(ps.find_output_pin('Pose'), tm.find_input_pin('A')); link(pc.find_output_pin('Pose'), tm.find_input_pin('B'))
    alpha_src = tw0.find_input_pin('Alpha').list_connected_pins()[0]; link(alpha_src, tm.find_input_pin('Alpha'))
    tf = ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Conv_BoolToDouble'); tf.rename(uniq('ToF'))
    link(andtp.find_output_pin('ReturnValue'), tf.find_input_pin('InBool'))
    sel = mk('애니메이션|블렌드|양방향블렌드', (-1600, 3000), 'PistolSelect')
    link(tw0.find_output_pin('Pose'), sel.find_input_pin('A')); link(tm.find_output_pin('Pose'), sel.find_input_pin('B')); link(tf.find_output_pin('ReturnValue'), sel.find_input_pin('Alpha'))
    consumers = [c for c in tw0.find_output_pin('Pose').list_connected_pins() if c.get_owning_node() != sel]
    R['consumers'] = [c.get_owning_node().get_name()[:34] + '.' + str(c.get_pin_name()) for c in consumers]
    for c in consumers:
        c.break_pin_links(); link(sel.find_output_pin('Pose'), c)
    BEL.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
    if abp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = EAL.save_asset('/Game/Furina/ABP_Furina', False)
except Exception: R['error'] = traceback.format_exc()[-1100:]
print('P220_ABP_LOCO', json.dumps(R, default=str, ensure_ascii=False))
