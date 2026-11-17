"""P200 그래프 작업용 공용 헬퍼 (pawn EventGraph). exec() 로 불러 쓴다."""
import unreal, traceback
PL = unreal.BlueprintGraphPinLibrary; BEL = unreal.BlueprintEditorLibrary; EAL = unreal.EditorAssetLibrary
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
KML = '/Script/Engine.KismetMathLibrary:'
bp = unreal.load_asset(PAWN)
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
CLS = bp.generated_class().get_path_name()
def N():
    return {x.get_name(): x for x in ed.list_all_nodes()}
def node(name): return N().get(name)
def link(a, b):
    assert a is not None and b is not None, 'null pin'
    assert a.is_valid() and b.is_valid(), 'invalid pin'
    assert PL.try_create_connection(a, b), 'link failed %s.%s -> %s.%s' % (a.get_owning_node().get_name(), a.get_pin_name(), b.get_owning_node().get_name(), b.get_pin_name())
import uuid
_seq = [0]
def uniq(prefix):
    _seq[0] += 1     # 실행마다 카운터가 초기화되므로 고유 접미사를 붙여 이름 충돌(에디터 크래시)을 막는다
    return 'P2_%s_%s%d' % (prefix, uuid.uuid4().hex[:6], _seq[0])
def fn(path, prefix=None):
    n = ed.add_call_function_node(path); assert n, 'call node ' + path
    n.rename(uniq(prefix or path.split(':')[-1])); return n
def lit(v):
    n = fn('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble', 'LitD'); n.find_input_pin('Value').set_pin_value(repr(float(v))); return n.find_result_pin()
def litint(v):
    n = fn('/Script/Engine.KismetSystemLibrary:MakeLiteralInt', 'LitI'); n.find_input_pin('Value').set_pin_value(str(int(v))); return n.find_result_pin()
def fval(pin, v):
    """float 입력핀에 값 넣기 (핀 값 설정이 무시되면 상수 노드 연결)"""
    pin.set_pin_value(repr(float(v)))
    try: ok = abs(float(str(pin.get_pin_value())) - float(v)) < 1e-6
    except Exception: ok = False
    if not ok:
        pin.break_pin_links(); link(lit(v), pin)
def ival(pin, v):
    pin.set_pin_value(str(int(v)))
    if str(pin.get_pin_value()) != str(int(v)):
        pin.break_pin_links(); link(litint(v), pin)
def getvar(name):
    n = ed.add_get_member_variable_node(name, CLS); assert n, 'getvar ' + name; n.rename(uniq('Get' + name))
    return n.find_output_pin(name)
def comp_get(name):
    n = ed.add_get_member_variable_node(name, CLS); assert n, 'getcomp ' + name; n.rename(uniq('Get' + name)); return n.find_output_pin(name)
def setvar(name):
    n = ed.add_set_member_variable_node(name, CLS); assert n, 'setvar ' + name; n.rename(uniq('Set' + name)); return n
def is_active(flag):
    g = comp_get(flag); f = fn('/Script/Engine.ActorComponent:IsActive', 'IsActive' + flag); link(g, f.find_self_pin()); return f.find_result_pin()
def set_active(flag, on):
    g = comp_get(flag); s = fn('/Script/Engine.ActorComponent:SetActive', 'SetActive' + flag); link(g, s.find_self_pin())
    s.find_input_pin('bNewActive').set_pin_value('true' if on else 'false'); return s
def branch(cond):
    b = ed.add_branch_node(); b.rename(uniq('Branch')); link(cond, b.find_condition_pin() if hasattr(b, 'find_condition_pin') else b.find_input_pin('Condition')); return b
def timer(func, t, loop=False):
    n = fn('/Script/Engine.KismetSystemLibrary:K2_SetTimer', 'Timer_' + func); n.find_input_pin('FunctionName').set_pin_value(func)
    fval(n.find_input_pin('Time'), t); n.find_input_pin('bLooping').set_pin_value('true' if loop else 'false')
    n.find_input_pin('InitialStartDelay').set_pin_value('0.0'); return n
def band(a, b):
    n = fn(KML + 'BooleanAND', 'And'); link(a, n.find_input_pin('A')); link(b, n.find_input_pin('B')); return n.find_result_pin()
def bor(a, b):
    n = fn(KML + 'BooleanOR', 'Or'); link(a, n.find_input_pin('A')); link(b, n.find_input_pin('B')); return n.find_result_pin()
def bnot(a):
    n = fn(KML + 'Not_PreBool', 'Not'); link(a, n.find_input_pin('A')); return n.find_result_pin()
def selfloat(a, b, pick):
    n = fn(KML + 'SelectFloat', 'SelF'); fval(n.find_input_pin('A'), a); fval(n.find_input_pin('B'), b); link(pick, n.find_input_pin('bPickA')); return n.find_result_pin()
def selint(a, b, pick):
    n = fn(KML + 'SelectInt', 'SelI'); ival(n.find_input_pin('A'), a); ival(n.find_input_pin('B'), b); link(pick, n.find_input_pin('bPickA')); return n.find_result_pin()
def mulf(a_pin, b_pin):
    n = fn(KML + 'Multiply_DoubleDouble', 'Mul'); link(a_pin, n.find_input_pin('A')); link(b_pin, n.find_input_pin('B')); return n.find_result_pin()
def addf(a_pin, b_pin):
    n = fn(KML + 'Add_DoubleDouble', 'Add'); link(a_pin, n.find_input_pin('A')); link(b_pin, n.find_input_pin('B')); return n.find_result_pin()
def mkvec(x, y, z):
    n = fn(KML + 'MakeVector', 'MkVec')
    for k, v in (('X', x), ('Y', y), ('Z', z)):
        if isinstance(v, (int, float)): fval(n.find_input_pin(k), v)
        else: link(v, n.find_input_pin(k))
    return n.find_result_pin()
def mkrot(roll, pitch, yaw):
    n = fn(KML + 'MakeRotator', 'MkRot')
    for k, v in (('Roll', roll), ('Pitch', pitch), ('Yaw', yaw)):
        if isinstance(v, (int, float)): fval(n.find_input_pin(k), v)
        else: link(v, n.find_input_pin(k))
    return n.find_result_pin()
def chain(*nodes):
    for a, b in zip(nodes, nodes[1:]): link(a.find_then_pin(), b.find_execute_pin())
def cleanup():
    old = [n for k, n in N().items() if k.startswith('P2_')]
    if old: ed.remove_nodes(old)
    return len(old)
