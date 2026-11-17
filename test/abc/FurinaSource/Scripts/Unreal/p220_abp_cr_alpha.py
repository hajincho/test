"""ABP_Furina: 3인칭 + 권총 장착일 때만 Control Rig(소총 그립 IK) Alpha 0 -> 입력 포즈(DefaultSlot 몽타주 = 리타게팅한 Lyra 권총 애니)를 그대로 사용. 1인칭은 변경 없음.
 Alpha <- ToFloat( NOT( IsActive(FurinaPistolOn) AND NotFP ) )   (NotFP = 기존 K2Node_FPVW_NotFP).  백업: FurinaSource/Backup_before_p200/ABP_Furina.uasset"""
import unreal, json, uuid, traceback
PL = unreal.BlueprintGraphPinLibrary; BEL = unreal.BlueprintEditorLibrary
R = {}
abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph')
def node(n): return next((x for x in ed.list_all_nodes() if x.get_name() == n), None)
def link(a, b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(), 'pin'
    assert PL.try_create_connection(a, b), 'link %s.%s -> %s.%s' % (a.get_owning_node().get_name(), a.get_pin_name(), b.get_owning_node().get_name(), b.get_pin_name())
def fn(path, prefix):
    n = ed.add_call_function_node(path); assert n, path; n.rename('P220_%s_%s' % (prefix, uuid.uuid4().hex[:6])); return n
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    cr = node('AnimGraphNode_ControlRig_0'); owner = node('K2Node_FPAA_Owner'); notfp = node('K2Node_FPVW_NotFP')
    f = fn('/Script/Engine.Actor:FindComponentByTag', 'FindPistol'); link(owner.find_output_pin('ReturnValue'), f.find_input_pin('self'))
    f.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); f.find_input_pin('Tag').set_pin_value('FurinaPistolOn')
    act = fn('/Script/Engine.ActorComponent:IsActive', 'IsPistol'); link(f.find_output_pin('ReturnValue'), act.find_input_pin('self'))
    an = fn('/Script/Engine.KismetMathLibrary:BooleanAND', 'AndTP'); link(act.find_output_pin('ReturnValue'), an.find_input_pin('A')); link(notfp.find_output_pin('ReturnValue'), an.find_input_pin('B'))
    nt = fn('/Script/Engine.KismetMathLibrary:Not_PreBool', 'NotTP'); link(an.find_output_pin('ReturnValue'), nt.find_input_pin('A'))
    tf = fn('/Script/Engine.KismetMathLibrary:Conv_BoolToDouble', 'ToF'); link(nt.find_output_pin('ReturnValue'), tf.find_input_pin('InBool'))
    link(tf.find_output_pin('ReturnValue'), cr.find_input_pin('Alpha'))
    BEL.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
except Exception: R['error'] = traceback.format_exc()[-1000:]
print('P220_ABP', json.dumps(R, default=str, ensure_ascii=False))
