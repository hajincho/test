"""Event-graph nodes for mouse-wheel camera zoom on ThirdPersonCharacter_BP (CameraBoom.TargetArmLength)."""
import uuid, sys
OUT = sys.argv[1]
STEP, MIN_LEN, MAX_LEN = 60.0, 200.0, 1600.0
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,'
END = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
ARM = "/Script/CoreUObject.Class'/Script/Engine.SpringArmComponent'"
MATH = "/Script/CoreUObject.Class'/Script/Engine.KismetMathLibrary'"
def pin(pid, name, cat, sub='', obj='None', out=False, default=None, link=None, hidden=False):
    s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (pid, name)
    if out: s += 'Direction="EGPD_Output",'
    s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,' % (cat, sub, obj if obj == 'None' else '"%s"' % obj)
    s += TAIL
    if default is not None: s += 'DefaultValue="%s",' % default
    if link: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in link)
    e = END.replace('bHidden=False', 'bHidden=True') if hidden else END
    return s + e
p = {k: g() for k in ['trig', 'aval', 'boom', 'lself', 'lval', 'ma', 'mb', 'mr', 'aa', 'ab', 'ar', 'cv', 'cmin', 'cmax', 'cr', 'sx', 'sthen', 'sval', 'sself', 'mself', 'aself', 'cself', 'sout']}
N = {'eia': 'K2Node_EnhancedInputAction_Zoom', 'boom': 'K2Node_VariableGet_ZoomBoom', 'len': 'K2Node_VariableGet_ZoomLen',
     'mul': 'K2Node_CallFunction_ZoomMul', 'add': 'K2Node_CallFunction_ZoomAdd', 'clamp': 'K2Node_CallFunction_ZoomClamp', 'set': 'K2Node_VariableSet_ZoomSet'}
X, Y = -2600, 16400
nodes = []
nodes.append(('/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', N['eia'], [
    "InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/IA_CameraZoom.IA_CameraZoom'\""], X, Y, [
    pin(p['trig'], 'Triggered', 'exec', out=True, link=[(N['set'], p['sx'])]),
    pin(p['aval'], 'ActionValue', 'real', 'double', out=True, default='0.0', link=[(N['mul'], p['ma'])])]))
nodes.append(('/Script/BlueprintGraph.K2Node_VariableGet', N['boom'], ['VariableReference=(MemberName="CameraBoom",bSelfContext=True)'], X, Y + 260, [
    pin(p['boom'], 'CameraBoom', 'object', obj=ARM, out=True, link=[(N['len'], p['lself']), (N['set'], p['sself'])])]))
nodes.append(('/Script/BlueprintGraph.K2Node_VariableGet', N['len'], ['VariableReference=(MemberParent="%s",MemberName="TargetArmLength")' % ARM, 'SelfContextInfo=NotSelfContext'], X + 260, Y + 340, [
    pin(p['lval'], 'TargetArmLength', 'real', 'float', out=True, default='0.0', link=[(N['add'], p['aa'])]),
    pin(p['lself'], 'self', 'object', obj=ARM, link=[(N['boom'], p['boom'])])]))
def call(name, func, x, y, pins):
    return ('/Script/BlueprintGraph.K2Node_CallFunction', name, ['bDefaultsToPureFunc=True', 'FunctionReference=(MemberParent="%s",MemberName="%s")' % (MATH, func)], x, y, pins)
nodes.append(call(N['mul'], 'Multiply_DoubleDouble', X + 300, Y + 120, [
    pin(p['ma'], 'A', 'real', 'double', default='0.0', link=[(N['eia'], p['aval'])]),
    pin(p['mb'], 'B', 'real', 'double', default='%f' % -STEP),
    pin(p['mr'], 'ReturnValue', 'real', 'double', out=True, default='0.0', link=[(N['add'], p['ab'])])]))
nodes.append(call(N['add'], 'Add_DoubleDouble', X + 560, Y + 220, [
    pin(p['aa'], 'A', 'real', 'double', default='0.0', link=[(N['len'], p['lval'])]),
    pin(p['ab'], 'B', 'real', 'double', default='0.0', link=[(N['mul'], p['mr'])]),
    pin(p['ar'], 'ReturnValue', 'real', 'double', out=True, default='0.0', link=[(N['clamp'], p['cv'])])]))
nodes.append(call(N['clamp'], 'FClamp', X + 800, Y + 220, [
    pin(p['cv'], 'Value', 'real', 'double', default='0.0', link=[(N['add'], p['ar'])]),
    pin(p['cmin'], 'Min', 'real', 'double', default='%f' % MIN_LEN),
    pin(p['cmax'], 'Max', 'real', 'double', default='%f' % MAX_LEN),
    pin(p['cr'], 'ReturnValue', 'real', 'double', out=True, default='0.0', link=[(N['set'], p['sval'])])]))
nodes.append(('/Script/BlueprintGraph.K2Node_VariableSet', N['set'], ['VariableReference=(MemberParent="%s",MemberName="TargetArmLength")' % ARM, 'SelfContextInfo=NotSelfContext'], X + 1060, Y, [
    pin(p['sx'], 'execute', 'exec', link=[(N['eia'], p['trig'])]),
    pin(p['sthen'], 'then', 'exec', out=True),
    pin(p['sval'], 'TargetArmLength', 'real', 'float', default='0.0', link=[(N['clamp'], p['cr'])]),
    pin(p['sself'], 'self', 'object', obj=ARM, link=[(N['boom'], p['boom'])])]))
out = []
for cls, name, props, x, y, pins in nodes:
    out.append('Begin Object Class=%s Name="%s"' % (cls, name))
    out += ['   ' + q for q in props]
    out += ['   NodePosX=%d' % x, '   NodePosY=%d' % y, '   NodeGuid=%s' % g()]
    out += ['   ' + q for q in pins]
    out.append('End Object')
out.append('Begin Object Class=/Script/UnrealEd.EdGraphNode_Comment Name="EdGraphNode_Comment_Zoom"')
out += ['   NodePosX=%d' % (X - 40), '   NodePosY=%d' % (Y - 80), '   NodeWidth=1500', '   NodeHeight=560',
        '   NodeComment="Mouse wheel camera zoom (Furina)"', '   NodeGuid=%s' % g(), 'End Object']
open(OUT, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')
print('ok')
