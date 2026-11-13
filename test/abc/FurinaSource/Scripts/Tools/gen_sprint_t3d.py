"""Event-graph nodes: hold Shift (IA_FurinaSprint) -> MaxWalkSpeed sprint, release -> walk (Unity ThirdPersonMotor)."""
import uuid, sys
OUT = sys.argv[1]
WALK, SPRINT = 120.0, 600.0
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,'
END = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
CMC = "/Script/CoreUObject.Class'/Script/Engine.CharacterMovementComponent'"
def pin(pid, name, cat, sub='', obj='None', out=False, default=None, link=None):
    s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (pid, name)
    if out: s += 'Direction="EGPD_Output",'
    s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,' % (cat, sub, obj if obj == 'None' else '"%s"' % obj)
    s += TAIL
    if default is not None: s += 'DefaultValue="%s",' % default
    if link: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in link)
    return s + END
p = {k: g() for k in ['trig', 'start', 'ong', 'canc', 'comp', 'aval', 'cmc', 'sx1', 'st1', 'sv1', 'ss1', 'sx2', 'st2', 'sv2', 'ss2']}
N = {'eia': 'K2Node_EnhancedInputAction_FSprint', 'cmc': 'K2Node_VariableGet_FSprintCMC', 'on': 'K2Node_VariableSet_FSprintOn', 'off': 'K2Node_VariableSet_FSprintOff'}
X, Y = -2600, 17200
nodes = [
 ('/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', N['eia'], ["InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/IA_FurinaSprint.IA_FurinaSprint'\""], X, Y, [
    pin(p['trig'], 'Triggered', 'exec', out=True),
    pin(p['start'], 'Started', 'exec', out=True, link=[(N['on'], p['sx1'])]),
    pin(p['ong'], 'Ongoing', 'exec', out=True),
    pin(p['canc'], 'Canceled', 'exec', out=True, link=[(N['off'], p['sx2'])]),
    pin(p['comp'], 'Completed', 'exec', out=True, link=[(N['off'], p['sx2'])]),
    pin(p['aval'], 'ActionValue', 'bool', out=True, default='false')]),
 ('/Script/BlueprintGraph.K2Node_VariableGet', N['cmc'], ['VariableReference=(MemberName="CharacterMovement",bSelfContext=True)'], X, Y + 320, [
    pin(p['cmc'], 'CharacterMovement', 'object', obj=CMC, out=True, link=[(N['on'], p['ss1']), (N['off'], p['ss2'])])]),
]
for key, sx, st, sv, ss, val, y in ((N['on'], 'sx1', 'st1', 'sv1', 'ss1', SPRINT, Y - 40), (N['off'], 'sx2', 'st2', 'sv2', 'ss2', WALK, Y + 200)):
    nodes.append(('/Script/BlueprintGraph.K2Node_VariableSet', key, ['VariableReference=(MemberParent="%s",MemberName="MaxWalkSpeed")' % CMC, 'SelfContextInfo=NotSelfContext'], X + 520, y, [
        pin(p[sx], 'execute', 'exec', link=[(N['eia'], p['start'] if key == N['on'] else p['comp'])] + ([] if key == N['on'] else [(N['eia'], p['canc'])])),
        pin(p[st], 'then', 'exec', out=True),
        pin(p[sv], 'MaxWalkSpeed', 'real', 'float', default='%f' % val),
        pin(p[ss], 'self', 'object', obj=CMC, link=[(N['cmc'], p['cmc'])])]))
out = []
for cls, name, props, x, y, pins in nodes:
    out.append('Begin Object Class=%s Name="%s"' % (cls, name))
    out += ['   ' + q for q in props]
    out += ['   NodePosX=%d' % x, '   NodePosY=%d' % y, '   NodeGuid=%s' % g()]
    out += ['   ' + q for q in pins]
    out.append('End Object')
out.append('Begin Object Class=/Script/UnrealEd.EdGraphNode_Comment Name="EdGraphNode_Comment_FSprint"')
out += ['   NodePosX=%d' % (X - 40), '   NodePosY=%d' % (Y - 120), '   NodeWidth=1000', '   NodeHeight=600',
        '   NodeComment="Shift = sprint (Furina, Unity ThirdPersonMotor walk 1.2 / sprint 6 m/s)"', '   NodeGuid=%s' % g(), 'End Object']
open(OUT, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')
print('ok')
