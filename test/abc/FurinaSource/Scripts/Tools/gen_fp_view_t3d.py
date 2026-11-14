"""Character EventGraph nodes: chosen view (V) vs forced third person during traversal moves.
  V (IA_FurinaViewToggle) -> FurinaFPWanted.ToggleActive()            (the component's active flag stores the chosen view)
  Controller changed       -> SetTimer(FurinaViewUpdate, 0.05 s, looping)
  FurinaViewUpdate:
    forced  = rail || zipline || rail jump || (not on ground && speed > 800)   (Grind_Rail_Component_BP flags, movement)
    desired = FurinaFPWanted.IsActive && !forced ;  current = FPCamera.IsActive
    desired != current -> switch (cameras, Head bone, rotation settings) exactly like the old V handler
usage: gen_fp_view_t3d.py <out t3d>"""
import uuid, sys
OUT = sys.argv[1]
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PinType.PinSubCategoryMemberReference=%s,PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,'
END = 'PersistentGuid=00000000000000000000000000000000,bHidden=%s,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
CLS = lambda p: "/Script/CoreUObject.Class'%s'" % p
BPC = lambda p: "/Script/Engine.BlueprintGeneratedClass'%s'" % p
STR = lambda p: "/Script/CoreUObject.ScriptStruct'%s'" % p
ENUM = lambda p: "/Script/CoreUObject.Enum'%s'" % p
E = '/Script/Engine.'
GRIND = '/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP.Grind_Rail_Component_BP_C'
class Graph:
    def __init__(self): self.nodes = {}; self.order = []
    def node(self, key, cls, props, x, y):
        self.nodes[key] = dict(cls=cls, name='K2Node_FPV_%s' % key, props=props, x=x, y=y, pins=[]); self.order.append(key); return key
    def pin(self, key, name, cat, sub='', obj=None, out=False, default=None, hidden=False, member='()'):
        self.nodes[key]['pins'].append(dict(id=g(), name=name, cat=cat, sub=sub, obj=obj, out=out, default=default, hidden=hidden, member=member, links=[]))
        return (key, name)
    def find(self, ref):
        for p in self.nodes[ref[0]]['pins']:
            if p['name'] == ref[1]: return p
        raise KeyError(ref)
    def link(self, a, b):
        pa, pb = self.find(a), self.find(b)
        pa['links'].append((self.nodes[b[0]]['name'], pb['id'])); pb['links'].append((self.nodes[a[0]]['name'], pa['id']))
    def text(self):
        out = []
        for key in self.order:
            n = self.nodes[key]
            out.append('Begin Object Class=%s Name="%s"' % (n['cls'], n['name']))
            out += ['   ' + q for q in n['props']] + ['   NodePosX=%d' % n['x'], '   NodePosY=%d' % n['y'], '   NodeGuid=%s' % g()]
            for p in n['pins']:
                s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (p['id'], p['name'])
                if p['out']: s += 'Direction="EGPD_Output",'
                s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,' % (p['cat'], p['sub'], ('"%s"' % p['obj']) if p['obj'] else 'None')
                s += TAIL % p['member']
                if p['default'] is not None: s += 'DefaultValue="%s",' % p['default']
                if p['links']: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in p['links'])
                out.append('   ' + s + END % ('True' if p['hidden'] else 'False'))
            out.append('End Object')
        return '\n'.join(out) + '\n'
G = Graph()
def call(key, owner, func, x, y, pure=False, self_cls=None, self_link=None):
    props = ['FunctionReference=(MemberParent="%s",MemberName="%s")' % (CLS(owner), func)]
    if pure: props.insert(0, 'bIsPureFunc=True')
    G.node(key, '/Script/BlueprintGraph.K2Node_CallFunction', props, x, y)
    if not pure: G.pin(key, 'execute', 'exec'); G.pin(key, 'then', 'exec', out=True)
    if self_cls:
        G.pin(key, 'self', 'object', obj=CLS(self_cls))
        if self_link: G.link(self_link, (key, 'self'))
    return key
def var_get(key, member, cls_obj, x, y):
    G.node(key, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member], x, y)
    return G.pin(key, member, 'object', obj=cls_obj, out=True)
def math2(key, func, a, b, x, y, cat='bool', sub='', out_cat='bool', out_sub=''):
    call(key, E + 'KismetMathLibrary', func, x, y, pure=True)
    G.pin(key, 'A', cat, sub, default='false' if cat == 'bool' else '0.0'); G.link(a, (key, 'A'))
    G.pin(key, 'B', cat, sub, default='false' if cat == 'bool' else '0.0')
    if b is not None: G.link(b, (key, 'B'))
    G.pin(key, 'ReturnValue', out_cat, out_sub, out=True)
    return (key, 'ReturnValue')
def chain(*keys):
    for a, b in zip(keys, keys[1:]): G.link((a, 'then'), (b, 'execute'))
X, Y = -2600, 22400
# ---- V: store the chosen view
G.node('ViewIA', '/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', ["InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/IA_FurinaViewToggle.IA_FurinaViewToggle'\""], X, Y)
for p in ('Triggered', 'Started', 'Ongoing', 'Canceled', 'Completed'): G.pin('ViewIA', p, 'exec', out=True)
G.pin('ViewIA', 'ActionValue', 'bool', out=True, default='false')
want = var_get('GetWant', 'FurinaFPWanted', CLS(E + 'SceneComponent'), X + 100, Y + 250)
call('Toggle', E + 'ActorComponent', 'ToggleActive', X + 400, Y, self_cls=E + 'ActorComponent', self_link=want)
G.link(('ViewIA', 'Started'), ('Toggle', 'execute'))
# ---- timer started whenever the pawn gets its controller
G.node('Ctrl', '/Script/BlueprintGraph.K2Node_Event', ['EventReference=(MemberParent="%s",MemberName="ReceiveControllerChanged")' % CLS(E + 'Pawn'), 'bOverrideFunction=True'], X, Y + 500)
G.pin('Ctrl', 'OutputDelegate', 'delegate', out=True, hidden=True); G.pin('Ctrl', 'then', 'exec', out=True)
G.pin('Ctrl', 'Pawn', 'object', obj=CLS(E + 'Pawn'), out=True)
G.pin('Ctrl', 'OldController', 'object', obj=CLS(E + 'Controller'), out=True); G.pin('Ctrl', 'NewController', 'object', obj=CLS(E + 'Controller'), out=True)
G.node('Upd', '/Script/BlueprintGraph.K2Node_CustomEvent', ['CustomFunctionName="FurinaViewUpdate"'], X, Y + 800)
G.pin('Upd', 'OutputDelegate', 'delegate', out=True, member='(MemberParent="%s",MemberName="FurinaViewUpdate")' % BPC('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP.ThirdPersonCharacter_BP_C'))
G.pin('Upd', 'then', 'exec', out=True)
call('Timer', E + 'KismetSystemLibrary', 'K2_SetTimerDelegate', X + 400, Y + 500)
G.pin('Timer', 'Delegate', 'delegate', member='(MemberParent="/Script/CoreUObject.Package\'/Script/Engine\'",MemberName="TimerDelegate__DelegateSignature")')
G.link(('Upd', 'OutputDelegate'), ('Timer', 'Delegate'))   # shown as 'Event' in the editor
G.pin('Timer', 'Time', 'real', 'float', default='0.050000'); G.pin('Timer', 'bLooping', 'bool', default='true')
G.pin('Timer', 'InitialStartDelay', 'real', 'float', default='0.000000'); G.pin('Timer', 'InitialStartDelayVariance', 'real', 'float', default='0.000000')
G.pin('Timer', 'ReturnValue', 'struct', obj=STR(E + 'TimerHandle'), out=True)
G.link(('Ctrl', 'then'), ('Timer', 'execute'))
# ---- conditions
grind = var_get('GetGrind', 'Grind_Rail_Component_BP', BPC(GRIND), X + 100, Y + 1100)
flags = []
for i, f in enumerate(('UsingRail?', 'UsingZipline?', 'RailJumpActive?')):
    k = 'Flag%d' % i
    G.node(k, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberParent="%s",MemberName="%s")' % (BPC(GRIND), f), 'SelfContextInfo=NotSelfContext'], X + 400, Y + 1050 + i * 120)
    G.pin(k, f, 'bool', out=True, default='false'); G.pin(k, 'self', 'object', obj=BPC(GRIND)); G.link(grind, (k, 'self'))
    flags.append((k, f))
cmc = var_get('GetCMC', 'CharacterMovement', CLS(E + 'CharacterMovementComponent'), X + 100, Y + 1500)
call('OnGround', E + 'NavMovementComponent', 'IsMovingOnGround', X + 400, Y + 1500, pure=True, self_cls=E + 'NavMovementComponent', self_link=cmc)
G.pin('OnGround', 'ReturnValue', 'bool', out=True)
call('Vel', E + 'Actor', 'GetVelocity', X + 400, Y + 1650, pure=True)
G.pin('Vel', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call('Speed', E + 'KismetMathLibrary', 'VSize', X + 650, Y + 1650, pure=True)
G.pin('Speed', 'A', 'struct', obj=STR('/Script/CoreUObject.Vector')); G.link(('Vel', 'ReturnValue'), ('Speed', 'A'))
G.pin('Speed', 'ReturnValue', 'real', 'double', out=True)
fast = math2('Fast', 'Greater_DoubleDouble', ('Speed', 'ReturnValue'), None, X + 900, Y + 1650, cat='real', sub='double')
G.find(('Fast', 'B'))['default'] = '800.0'
call('NotGround', E + 'KismetMathLibrary', 'Not_PreBool', X + 650, Y + 1500, pure=True)
G.pin('NotGround', 'A', 'bool', default='false'); G.link(('OnGround', 'ReturnValue'), ('NotGround', 'A')); G.pin('NotGround', 'ReturnValue', 'bool', out=True)
air = math2('AirFast', 'BooleanAND', ('NotGround', 'ReturnValue'), fast, X + 1150, Y + 1550)
o1 = math2('Or1', 'BooleanOR', flags[0], flags[1], X + 700, Y + 1100)
o2 = math2('Or2', 'BooleanOR', o1, flags[2], X + 950, Y + 1150)
forced = math2('Forced', 'BooleanOR', o2, air, X + 1400, Y + 1250)
want2 = var_get('GetWant2', 'FurinaFPWanted', CLS(E + 'SceneComponent'), X + 1150, Y + 900)
call('WantFP', E + 'ActorComponent', 'IsActive', X + 1400, Y + 900, pure=True, self_cls=E + 'ActorComponent', self_link=want2)
G.pin('WantFP', 'ReturnValue', 'bool', out=True)
call('NotForced', E + 'KismetMathLibrary', 'Not_PreBool', X + 1650, Y + 1250, pure=True)
G.pin('NotForced', 'A', 'bool', default='false'); G.link(forced, ('NotForced', 'A')); G.pin('NotForced', 'ReturnValue', 'bool', out=True)
desired = math2('Desired', 'BooleanAND', ('WantFP', 'ReturnValue'), ('NotForced', 'ReturnValue'), X + 1900, Y + 1050)
cam = var_get('GetFPCam', 'FPCamera', CLS(E + 'CameraComponent'), X + 1650, Y + 700)
call('IsFP', E + 'ActorComponent', 'IsActive', X + 1900, Y + 700, pure=True, self_cls=E + 'ActorComponent', self_link=cam)
G.pin('IsFP', 'ReturnValue', 'bool', out=True)
differs = math2('Differs', 'NotEqual_BoolBool', desired, ('IsFP', 'ReturnValue'), X + 2150, Y + 900)
def branch(key, cond, x, y):
    G.node(key, '/Script/BlueprintGraph.K2Node_IfThenElse', [], x, y)
    G.pin(key, 'execute', 'exec'); G.pin(key, 'Condition', 'bool', default='true'); G.pin(key, 'then', 'exec', out=True); G.pin(key, 'else', 'exec', out=True)
    G.link(cond, (key, 'Condition'))
branch('NeedSwitch', differs, X + 2400, Y + 800); G.link(('Upd', 'then'), ('NeedSwitch', 'execute'))
branch('CurFP', ('IsFP', 'ReturnValue'), X + 2650, Y + 800); G.link(('NeedSwitch', 'then'), ('CurFP', 'execute'))
# ---- the switch (same steps as the original V handler)
mesh = var_get('GetMesh', 'FurinaMesh', CLS(E + 'SkeletalMeshComponent'), X + 2700, Y + 1300)
follow = var_get('GetFollow', 'FollowCamera', CLS(E + 'CameraComponent'), X + 2700, Y + 1400)
cam2 = var_get('GetFPCam2', 'FPCamera', CLS(E + 'CameraComponent'), X + 2700, Y + 1500)
cmc2 = var_get('GetCMC2', 'CharacterMovement', CLS(E + 'CharacterMovementComponent'), X + 2700, Y + 1600)
def set_active(key, target, on, x, y):
    call(key, E + 'ActorComponent', 'SetActive', x, y, self_cls=E + 'ActorComponent', self_link=target)
    G.pin(key, 'bNewActive', 'bool', default='true' if on else 'false'); G.pin(key, 'bReset', 'bool', default='false')
def bone(key, hide, x, y):
    call(key, E + 'SkinnedMeshComponent', 'HideBoneByName' if hide else 'UnHideBoneByName', x, y, self_cls=E + 'SkinnedMeshComponent', self_link=mesh)
    G.pin(key, 'BoneName', 'name', default='Head')
    if hide: G.pin(key, 'PhysBodyOption', 'byte', obj=ENUM(E + 'EPhysBodyOp'), default='PBO_None')
def orient(key, on, x, y):
    G.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="bOrientRotationToMovement")' % CLS(E + 'CharacterMovementComponent'), 'SelfContextInfo=NotSelfContext'], x, y)
    G.pin(key, 'execute', 'exec'); G.pin(key, 'then', 'exec', out=True); G.pin(key, 'bOrientRotationToMovement', 'bool', default='true' if on else 'false')
    G.pin(key, 'self', 'object', obj=CLS(E + 'CharacterMovementComponent')); G.link(cmc2, (key, 'self'))
def yaw(key, on, x, y):
    G.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberName="bUseControllerRotationYaw",bSelfContext=True)'], x, y)
    G.pin(key, 'execute', 'exec'); G.pin(key, 'then', 'exec', out=True); G.pin(key, 'bUseControllerRotationYaw', 'bool', default='true' if on else 'false')
SX = X + 2950
set_active('TP_CamOff', cam2, False, SX, Y + 600); set_active('TP_FollowOn', follow, True, SX + 300, Y + 600)
bone('TP_Unhide', False, SX + 600, Y + 600); orient('TP_Orient', True, SX + 900, Y + 600); yaw('TP_Yaw', False, SX + 1200, Y + 600)
G.link(('CurFP', 'then'), ('TP_CamOff', 'execute')); chain('TP_CamOff', 'TP_FollowOn', 'TP_Unhide', 'TP_Orient', 'TP_Yaw')
set_active('FP_FollowOff', follow, False, SX, Y + 1000); set_active('FP_CamOn', cam2, True, SX + 300, Y + 1000)
bone('FP_Hide', True, SX + 600, Y + 1000); orient('FP_Orient', False, SX + 900, Y + 1000); yaw('FP_Yaw', True, SX + 1200, Y + 1000)
G.link(('CurFP', 'else'), ('FP_FollowOff', 'execute')); chain('FP_FollowOff', 'FP_CamOn', 'FP_Hide', 'FP_Orient', 'FP_Yaw')
open(OUT, 'w', encoding='utf-8', newline='\r\n').write(G.text())
print('ok', len(G.order))
