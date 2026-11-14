"""Blueprint nodes (text) for the rifle / first-person logic.
usage: gen_fp_bp_t3d.py <out character t3d> <out hud t3d>
Character EventGraph:
  Event Possessed -> attach FurinaRifle to FurinaMesh 'Right-wrist', FPCamera to 'Head' (keep relative) -> ClientSetHUD(BP_FurinaHUD)
  V (IA_FurinaView)   -> FPCamera active ? third person : first person (cameras, hide Head bone, controller yaw)
  Left mouse (Fire)   -> face the control yaw -> fire montage + rifle fire anim -> line trace from the camera ->
                          impulse on simulating physics bodies
  R (Reload)          -> reload montage + rifle reload anim
HUD EventGraph: ReceiveDrawHUD -> two crosshair lines at the screen centre."""
import uuid, sys
OUT_CHAR, OUT_HUD = sys.argv[1], sys.argv[2]
def g(): return uuid.uuid4().hex.upper()
TAIL = 'PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=%s,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,'
END = 'PersistentGuid=00000000000000000000000000000000,bHidden=%s,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
CLS = lambda p: "/Script/CoreUObject.Class'%s'" % p
STR = lambda p: "/Script/CoreUObject.ScriptStruct'%s'" % p
ENUM = lambda p: "/Script/CoreUObject.Enum'%s'" % p

class Graph:
    def __init__(self): self.nodes = {}; self.order = []
    def node(self, key, cls, props, x, y):
        self.nodes[key] = dict(cls=cls, name='K2Node_FP_%s' % key, props=props, x=x, y=y, pins=[])
        self.order.append(key); return key
    def pin(self, key, name, cat, sub='', obj=None, out=False, default=None, hidden=False, container='None', default_object=None):
        pid = g()
        self.nodes[key]['pins'].append(dict(id=pid, name=name, cat=cat, sub=sub, obj=obj, out=out, default=default, hidden=hidden,
                                            container=container, default_object=default_object, links=[]))
        return (key, name)
    def find(self, ref):
        key, name = ref
        for p in self.nodes[key]['pins']:
            if p['name'] == name: return p
        raise KeyError(ref)
    def link(self, a, b):
        pa, pb = self.find(a), self.find(b)
        pa['links'].append((self.nodes[b[0]]['name'], pb['id'])); pb['links'].append((self.nodes[a[0]]['name'], pa['id']))
    def text(self):
        out = []
        for key in self.order:
            n = self.nodes[key]
            out.append('Begin Object Class=%s Name="%s"' % (n['cls'], n['name']))
            out += ['   ' + q for q in n['props']]
            out += ['   NodePosX=%d' % n['x'], '   NodePosY=%d' % n['y'], '   NodeGuid=%s' % g()]
            for p in n['pins']:
                s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (p['id'], p['name'])
                if p['out']: s += 'Direction="EGPD_Output",'
                s += 'PinType.PinCategory="%s",PinType.PinSubCategory="%s",PinType.PinSubCategoryObject=%s,' % (p['cat'], p['sub'], ('"%s"' % p['obj']) if p['obj'] else 'None')
                s += TAIL % p['container']
                if p['default'] is not None: s += 'DefaultValue="%s",' % p['default']
                if p['default_object']: s += 'DefaultObject="%s",' % p['default_object']
                if p['links']: s += 'LinkedTo=(%s),' % ''.join('%s %s,' % l for l in p['links'])
                s += END % ('True' if p['hidden'] else 'False')
                out.append('   CustomProperties Pin ' + s[len('CustomProperties Pin '):])
            out.append('End Object')
        return '\n'.join(out) + '\n'

def call(G, key, owner, func, x, y, pure=False, self_cls=None, self_link=None):
    props = ['FunctionReference=(MemberParent="%s",MemberName="%s")' % (CLS(owner), func)]
    if pure: props.insert(0, 'bIsPureFunc=True')
    G.node(key, '/Script/BlueprintGraph.K2Node_CallFunction', props, x, y)
    if not pure:
        G.pin(key, 'execute', 'exec'); G.pin(key, 'then', 'exec', out=True)
    if self_cls:
        G.pin(key, 'self', 'object', obj=CLS(self_cls))
        if self_link: G.link(self_link, (key, 'self'))
    return key
def var_get(G, key, member, cls, x, y):
    G.node(key, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member], x, y)
    return G.pin(key, member, 'object', obj=CLS(cls), out=True)
def chain(G, *keys):
    for a, b in zip(keys, keys[1:]): G.link((a, 'then'), (b, 'execute'))

E = '/Script/Engine.'
# ======================= character graph
C = Graph()
X, Y = -2600, 18200
C.node('Poss', '/Script/BlueprintGraph.K2Node_Event', ['EventReference=(MemberParent="%s",MemberName="ReceivePossessed")' % CLS(E + 'Pawn'), 'bOverrideFunction=True'], X, Y)
C.pin('Poss', 'OutputDelegate', 'delegate', out=True, hidden=True); C.pin('Poss', 'then', 'exec', out=True)
C.pin('Poss', 'NewController', 'object', obj=CLS(E + 'Controller'), out=True)
rifle = var_get(C, 'GetRifle', 'FurinaRifle', E + 'SkeletalMeshComponent', X + 100, Y + 250)
mesh = var_get(C, 'GetMesh', 'FurinaMesh', E + 'SkeletalMeshComponent', X + 100, Y + 350)
cam = var_get(C, 'GetFPCam', 'FPCamera', E + 'CameraComponent', X + 100, Y + 450)
follow = var_get(C, 'GetFollow', 'FollowCamera', E + 'CameraComponent', X + 100, Y + 550)
def attach(key, target, socket, x):
    call(C, key, E + 'SceneComponent', 'K2_AttachToComponent', x, Y, self_cls=E + 'SceneComponent', self_link=target)
    C.pin(key, 'Parent', 'object', obj=CLS(E + 'SceneComponent')); C.link(mesh, (key, 'Parent'))
    C.pin(key, 'SocketName', 'name', default=socket)
    for r in ('LocationRule', 'RotationRule', 'ScaleRule'): C.pin(key, r, 'byte', obj=ENUM(E + 'EAttachmentRule'), default='KeepRelative')
    C.pin(key, 'bWeldSimulatedBodies', 'bool', default='false'); C.pin(key, 'ReturnValue', 'bool', out=True)
attach('AttachRifle', rifle, 'Right-wrist', X + 400)
attach('AttachCam', cam, 'Head', X + 750)
call(C, 'GetPC', E + 'GameplayStatics', 'GetPlayerController', X + 750, Y + 350, pure=True)
C.pin('GetPC', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
C.pin('GetPC', 'PlayerIndex', 'int', default='0'); pc = C.pin('GetPC', 'ReturnValue', 'object', obj=CLS(E + 'PlayerController'), out=True)
call(C, 'SetHUD', E + 'PlayerController', 'ClientSetHUD', X + 1100, Y, self_cls=E + 'PlayerController', self_link=pc)
C.pin('SetHUD', 'NewHUDClass', 'class', obj=CLS(E + 'HUD'), default_object='/Game/Furina/FP/BP_FurinaHUD.BP_FurinaHUD_C')
chain(C, 'Poss', 'AttachRifle', 'AttachCam', 'SetHUD')

# ---- V: toggle first / third person
VY = Y + 900
def eia(key, ia, x, y):
    C.node(key, '/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', ["InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/%s.%s'\"" % (ia, ia)], x, y)
    for p in ('Triggered', 'Started', 'Ongoing', 'Canceled', 'Completed'): C.pin(key, p, 'exec', out=True)
    C.pin(key, 'ActionValue', 'bool', out=True, default='false')
eia('ViewIA', 'IA_FurinaView', X, VY)
cam2 = var_get(C, 'GetFPCam2', 'FPCamera', E + 'CameraComponent', X + 100, VY + 250)
call(C, 'IsFP', E + 'ActorComponent', 'IsActive', X + 350, VY + 250, pure=True, self_cls=E + 'ActorComponent', self_link=cam2)
C.pin('IsFP', 'ReturnValue', 'bool', out=True)
C.node('ViewBranch', '/Script/BlueprintGraph.K2Node_IfThenElse', [], X + 350, VY)
C.pin('ViewBranch', 'execute', 'exec'); C.pin('ViewBranch', 'Condition', 'bool', default='true')
C.pin('ViewBranch', 'then', 'exec', out=True); C.pin('ViewBranch', 'else', 'exec', out=True)
C.link(('ViewIA', 'Started'), ('ViewBranch', 'execute')); C.link(('IsFP', 'ReturnValue'), ('ViewBranch', 'Condition'))
mesh2 = var_get(C, 'GetMesh2', 'FurinaMesh', E + 'SkeletalMeshComponent', X + 600, VY + 600)
follow2 = var_get(C, 'GetFollow2', 'FollowCamera', E + 'CameraComponent', X + 600, VY + 700)
cmc = var_get(C, 'GetCMC', 'CharacterMovement', E + 'CharacterMovementComponent', X + 600, VY + 800)
def set_active(key, target, on, x, y):
    call(C, key, E + 'ActorComponent', 'SetActive', x, y, self_cls=E + 'ActorComponent', self_link=target)
    C.pin(key, 'bNewActive', 'bool', default='true' if on else 'false'); C.pin(key, 'bReset', 'bool', default='false')
def bone(key, hide, x, y):
    call(C, key, E + 'SkinnedMeshComponent', 'HideBoneByName' if hide else 'UnHideBoneByName', x, y, self_cls=E + 'SkinnedMeshComponent', self_link=mesh2)
    C.pin(key, 'BoneName', 'name', default='Head')
    if hide: C.pin(key, 'PhysBodyOption', 'byte', obj=ENUM(E + 'EPhysBodyOp'), default='PBO_None')
def orient(key, on, x, y):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="bOrientRotationToMovement")' % CLS(E + 'CharacterMovementComponent'), 'SelfContextInfo=NotSelfContext'], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'then', 'exec', out=True)
    C.pin(key, 'bOrientRotationToMovement', 'bool', default='true' if on else 'false')
    C.pin(key, 'self', 'object', obj=CLS(E + 'CharacterMovementComponent')); C.link(cmc, (key, 'self'))
def yaw(key, on, x, y):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberName="bUseControllerRotationYaw",bSelfContext=True)'], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'then', 'exec', out=True)
    C.pin(key, 'bUseControllerRotationYaw', 'bool', default='true' if on else 'false')
# currently first person (branch true) -> go to third person
set_active('TP_CamOff', cam2, False, X + 650, VY - 150); set_active('TP_FollowOn', follow2, True, X + 950, VY - 150)
bone('TP_Unhide', False, X + 1250, VY - 150); orient('TP_Orient', True, X + 1550, VY - 150); yaw('TP_Yaw', False, X + 1850, VY - 150)
C.link(('ViewBranch', 'then'), ('TP_CamOff', 'execute')); chain(C, 'TP_CamOff', 'TP_FollowOn', 'TP_Unhide', 'TP_Orient', 'TP_Yaw')
# currently third person -> go to first person
set_active('FP_FollowOff', follow2, False, X + 650, VY + 150); set_active('FP_CamOn', cam2, True, X + 950, VY + 150)
bone('FP_Hide', True, X + 1250, VY + 150); orient('FP_Orient', False, X + 1550, VY + 150); yaw('FP_Yaw', True, X + 1850, VY + 150)
C.link(('ViewBranch', 'else'), ('FP_FollowOff', 'execute')); chain(C, 'FP_FollowOff', 'FP_CamOn', 'FP_Hide', 'FP_Orient', 'FP_Yaw')

# ---- Fire
FY = VY + 1100
eia('FireIA', 'IA_FurinaFire', X, FY)
call(C, 'CtrlRot', E + 'Pawn', 'GetControlRotation', X + 100, FY + 300, pure=True)
C.pin('CtrlRot', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Rotator'), out=True)
call(C, 'BreakCtrl', E + 'KismetMathLibrary', 'BreakRotator', X + 350, FY + 300, pure=True)
C.pin('BreakCtrl', 'InRot', 'struct', obj=STR('/Script/CoreUObject.Rotator')); C.link(('CtrlRot', 'ReturnValue'), ('BreakCtrl', 'InRot'))
for p in ('Roll', 'Pitch', 'Yaw'): C.pin('BreakCtrl', p, 'real', 'double', out=True)
call(C, 'MakeYaw', E + 'KismetMathLibrary', 'MakeRotator', X + 600, FY + 300, pure=True)
C.pin('MakeYaw', 'Roll', 'real', 'double', default='0.0'); C.pin('MakeYaw', 'Pitch', 'real', 'double', default='0.0')
C.pin('MakeYaw', 'Yaw', 'real', 'double', default='0.0'); C.link(('BreakCtrl', 'Yaw'), ('MakeYaw', 'Yaw'))
C.pin('MakeYaw', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Rotator'), out=True)
call(C, 'FaceAim', E + 'Actor', 'K2_SetActorRotation', X + 400, FY)
C.pin('FaceAim', 'NewRotation', 'struct', obj=STR('/Script/CoreUObject.Rotator')); C.link(('MakeYaw', 'ReturnValue'), ('FaceAim', 'NewRotation'))
C.pin('FaceAim', 'bTeleportPhysics', 'bool', default='false'); C.pin('FaceAim', 'ReturnValue', 'bool', out=True)
C.link(('FireIA', 'Started'), ('FaceAim', 'execute'))
mesh3 = var_get(C, 'GetMesh3', 'FurinaMesh', E + 'SkeletalMeshComponent', X + 700, FY + 450)
def montage(key, prefix, asset, x, y, mesh_ref):
    call(C, prefix + 'AnimInst', E + 'SkeletalMeshComponent', 'GetAnimInstance', x - 250, y + 250, pure=True, self_cls=E + 'SkeletalMeshComponent', self_link=mesh_ref)
    C.pin(prefix + 'AnimInst', 'ReturnValue', 'object', obj=CLS(E + 'AnimInstance'), out=True)
    call(C, key, E + 'AnimInstance', 'Montage_Play', x, y, self_cls=E + 'AnimInstance', self_link=(prefix + 'AnimInst', 'ReturnValue'))
    C.pin(key, 'MontageToPlay', 'object', obj=CLS(E + 'AnimMontage'), default_object='/Game/Furina/FP/Anim/%s.%s' % (asset, asset))
    C.pin(key, 'InPlayRate', 'real', 'float', default='1.000000')
    C.pin(key, 'ReturnValueType', 'byte', obj=ENUM(E + 'EMontagePlayReturnType'), default='MontageLength')
    C.pin(key, 'InTimeToStartMontageAt', 'real', 'float', default='0.000000'); C.pin(key, 'bStopAllMontages', 'bool', default='true')
    C.pin(key, 'ReturnValue', 'real', 'float', out=True)
def rifle_anim(key, asset, x, y, rifle_ref):
    call(C, key, E + 'SkeletalMeshComponent', 'PlayAnimation', x, y, self_cls=E + 'SkeletalMeshComponent', self_link=rifle_ref)
    C.pin(key, 'NewAnimToPlay', 'object', obj=CLS(E + 'AnimationAsset'), default_object='/Game/Furina/FP/Weapon/%s.%s' % (asset, asset))
    C.pin(key, 'bLooping', 'bool', default='false')
montage('FireMontage', 'Fire', 'AM_Furina_FP_Fire', X + 950, FY, mesh3)
rifle3 = var_get(C, 'GetRifle3', 'FurinaRifle', E + 'SkeletalMeshComponent', X + 1050, FY + 450)
rifle_anim('FireRifle', 'A_FP_WEP_AssaultRifle_Fire', X + 1300, FY, rifle3)
# trace from the camera through the crosshair
call(C, 'CamMgr', E + 'GameplayStatics', 'GetPlayerCameraManager', X + 1300, FY + 300, pure=True)
C.pin('CamMgr', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
C.pin('CamMgr', 'PlayerIndex', 'int', default='0'); cm = C.pin('CamMgr', 'ReturnValue', 'object', obj=CLS(E + 'PlayerCameraManager'), out=True)
call(C, 'CamLoc', E + 'PlayerCameraManager', 'GetCameraLocation', X + 1550, FY + 300, pure=True, self_cls=E + 'PlayerCameraManager', self_link=cm)
C.pin('CamLoc', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call(C, 'CamRot', E + 'PlayerCameraManager', 'GetCameraRotation', X + 1550, FY + 420, pure=True, self_cls=E + 'PlayerCameraManager', self_link=cm)
C.pin('CamRot', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Rotator'), out=True)
call(C, 'CamFwd', E + 'KismetMathLibrary', 'GetForwardVector', X + 1800, FY + 420, pure=True)
C.pin('CamFwd', 'InRot', 'struct', obj=STR('/Script/CoreUObject.Rotator')); C.link(('CamRot', 'ReturnValue'), ('CamFwd', 'InRot'))
C.pin('CamFwd', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call(C, 'FwdFar', E + 'KismetMathLibrary', 'Multiply_VectorFloat', X + 2050, FY + 420, pure=True)
C.pin('FwdFar', 'A', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('CamFwd', 'ReturnValue'), ('FwdFar', 'A'))
C.pin('FwdFar', 'B', 'real', 'double', default='20000.0'); C.pin('FwdFar', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call(C, 'TraceEnd', E + 'KismetMathLibrary', 'Add_VectorVector', X + 2300, FY + 350, pure=True)
C.pin('TraceEnd', 'A', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('CamLoc', 'ReturnValue'), ('TraceEnd', 'A'))
C.pin('TraceEnd', 'B', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('FwdFar', 'ReturnValue'), ('TraceEnd', 'B'))
C.pin('TraceEnd', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call(C, 'Trace', E + 'KismetSystemLibrary', 'LineTraceSingle', X + 1650, FY)
C.pin('Trace', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
C.pin('Trace', 'Start', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('CamLoc', 'ReturnValue'), ('Trace', 'Start'))
C.pin('Trace', 'End', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('TraceEnd', 'ReturnValue'), ('Trace', 'End'))
C.pin('Trace', 'TraceChannel', 'byte', obj=ENUM(E + 'ETraceTypeQuery'), default='TraceTypeQuery1')
C.pin('Trace', 'bTraceComplex', 'bool', default='false')
C.pin('Trace', 'ActorsToIgnore', 'object', obj=CLS(E + 'Actor'), container='Array')
C.pin('Trace', 'DrawDebugType', 'byte', obj=ENUM('/Script/Engine.EDrawDebugTrace'), default='ForDuration')
C.pin('Trace', 'OutHit', 'struct', obj=STR(E + 'HitResult'), out=True)
C.pin('Trace', 'bIgnoreSelf', 'bool', default='true')
C.pin('Trace', 'TraceColor', 'struct', obj=STR('/Script/CoreUObject.LinearColor'), default='(R=1.000000,G=0.800000,B=0.300000,A=1.000000)')
C.pin('Trace', 'TraceHitColor', 'struct', obj=STR('/Script/CoreUObject.LinearColor'), default='(R=1.000000,G=0.200000,B=0.200000,A=1.000000)')
C.pin('Trace', 'DrawTime', 'real', 'float', default='0.150000')
C.pin('Trace', 'ReturnValue', 'bool', out=True)
chain(C, 'FaceAim', 'FireMontage', 'FireRifle', 'Trace')
call(C, 'BreakHit', E + 'GameplayStatics', 'BreakHitResult', X + 1950, FY + 650, pure=True)
C.pin('BreakHit', 'Hit', 'struct', obj=STR(E + 'HitResult')); C.link(('Trace', 'OutHit'), ('BreakHit', 'Hit'))
for name, cat, obj, sub in (('bBlockingHit', 'bool', None, ''), ('bInitialOverlap', 'bool', None, ''), ('Time', 'real', None, 'float'), ('Distance', 'real', None, 'float'),
                            ('Location', 'struct', STR('/Script/CoreUObject.Vector'), ''), ('ImpactPoint', 'struct', STR('/Script/CoreUObject.Vector'), ''),
                            ('Normal', 'struct', STR('/Script/CoreUObject.Vector'), ''), ('ImpactNormal', 'struct', STR('/Script/CoreUObject.Vector'), ''),
                            ('PhysMat', 'object', CLS('/Script/PhysicsCore.PhysicalMaterial'), ''), ('HitActor', 'object', CLS(E + 'Actor'), ''),
                            ('HitComponent', 'object', CLS(E + 'PrimitiveComponent'), ''), ('HitBoneName', 'name', None, ''), ('BoneName', 'name', None, ''),
                            ('HitItem', 'int', None, ''), ('ElementIndex', 'int', None, ''), ('FaceIndex', 'int', None, ''),
                            ('TraceStart', 'struct', STR('/Script/CoreUObject.Vector'), ''), ('TraceEnd', 'struct', STR('/Script/CoreUObject.Vector'), '')):
    C.pin('BreakHit', name, cat, sub, obj=obj, out=True)
C.node('HitBranch', '/Script/BlueprintGraph.K2Node_IfThenElse', [], X + 1950, FY)
C.pin('HitBranch', 'execute', 'exec'); C.pin('HitBranch', 'Condition', 'bool', default='true')
C.pin('HitBranch', 'then', 'exec', out=True); C.pin('HitBranch', 'else', 'exec', out=True)
C.link(('Trace', 'then'), ('HitBranch', 'execute')); C.link(('Trace', 'ReturnValue'), ('HitBranch', 'Condition'))
call(C, 'IsSim', E + 'PrimitiveComponent', 'IsSimulatingPhysics', X + 2250, FY + 250, pure=True, self_cls=E + 'PrimitiveComponent', self_link=('BreakHit', 'HitComponent'))
C.pin('IsSim', 'BoneName', 'name', default='None'); C.pin('IsSim', 'ReturnValue', 'bool', out=True)
C.node('SimBranch', '/Script/BlueprintGraph.K2Node_IfThenElse', [], X + 2250, FY)
C.pin('SimBranch', 'execute', 'exec'); C.pin('SimBranch', 'Condition', 'bool', default='true')
C.pin('SimBranch', 'then', 'exec', out=True); C.pin('SimBranch', 'else', 'exec', out=True)
C.link(('HitBranch', 'then'), ('SimBranch', 'execute')); C.link(('IsSim', 'ReturnValue'), ('SimBranch', 'Condition'))
call(C, 'Push', E + 'PrimitiveComponent', 'AddImpulseAtLocation', X + 2550, FY, self_cls=E + 'PrimitiveComponent', self_link=('BreakHit', 'HitComponent'))
call(C, 'PushDir', E + 'KismetMathLibrary', 'Multiply_VectorFloat', X + 2550, FY + 300, pure=True)
C.pin('PushDir', 'A', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('CamFwd', 'ReturnValue'), ('PushDir', 'A'))
C.pin('PushDir', 'B', 'real', 'double', default='60000.0'); C.pin('PushDir', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
C.pin('Push', 'Impulse', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('PushDir', 'ReturnValue'), ('Push', 'Impulse'))
C.pin('Push', 'Location', 'struct', obj=STR('/Script/CoreUObject.Vector')); C.link(('BreakHit', 'ImpactPoint'), ('Push', 'Location'))
C.pin('Push', 'BoneName', 'name', default='None')
C.link(('SimBranch', 'then'), ('Push', 'execute'))

# ---- Reload
RY = FY + 1000
eia('ReloadIA', 'IA_FurinaReload', X, RY)
mesh4 = var_get(C, 'GetMesh4', 'FurinaMesh', E + 'SkeletalMeshComponent', X + 100, RY + 300)
montage('ReloadMontage', 'Reload', 'AM_Furina_FP_Reload', X + 600, RY, mesh4)
rifle4 = var_get(C, 'GetRifle4', 'FurinaRifle', E + 'SkeletalMeshComponent', X + 700, RY + 450)
rifle_anim('ReloadRifle', 'A_FP_WEP_AssaultRifle_Reload', X + 950, RY, rifle4)
C.link(('ReloadIA', 'Started'), ('ReloadMontage', 'execute')); chain(C, 'ReloadMontage', 'ReloadRifle')
open(OUT_CHAR, 'w', encoding='utf-8', newline='\r\n').write(C.text())

# ======================= HUD graph: crosshair
H = Graph()
H.node('Draw', '/Script/BlueprintGraph.K2Node_Event', ['EventReference=(MemberParent="%s",MemberName="ReceiveDrawHUD")' % CLS(E + 'HUD'), 'bOverrideFunction=True'], 0, 0)
H.pin('Draw', 'OutputDelegate', 'delegate', out=True, hidden=True); H.pin('Draw', 'then', 'exec', out=True)
H.pin('Draw', 'SizeX', 'int', out=True); H.pin('Draw', 'SizeY', 'int', out=True)
def half(key, src, x, y):
    call(H, key + 'D', E + 'KismetMathLibrary', 'Conv_IntToDouble', x, y, pure=True)
    H.pin(key + 'D', 'InInt', 'int', default='0'); H.link(('Draw', src), (key + 'D', 'InInt'))
    H.pin(key + 'D', 'ReturnValue', 'real', 'double', out=True)
    call(H, key, E + 'KismetMathLibrary', 'Multiply_DoubleDouble', x + 250, y, pure=True)
    H.pin(key, 'A', 'real', 'double', default='0.0'); H.link((key + 'D', 'ReturnValue'), (key, 'A'))
    H.pin(key, 'B', 'real', 'double', default='0.5'); H.pin(key, 'ReturnValue', 'real', 'double', out=True)
half('CX', 'SizeX', 0, 300); half('CY', 'SizeY', 0, 450)
def offs(key, src, d, x, y):
    call(H, key, E + 'KismetMathLibrary', 'Add_DoubleDouble', x, y, pure=True)
    H.pin(key, 'A', 'real', 'double', default='0.0'); H.link((src, 'ReturnValue'), (key, 'A'))
    H.pin(key, 'B', 'real', 'double', default='%f' % d); H.pin(key, 'ReturnValue', 'real', 'double', out=True)
offs('XL', 'CX', -11, 600, 250); offs('XR', 'CX', 11, 600, 350); offs('YT', 'CY', -11, 600, 450); offs('YB', 'CY', 11, 600, 550)
def line(key, sx, sy, ex, ey, x):
    call(H, key, E + 'HUD', 'DrawLine', x, 0)
    for pin_name, src in (('StartScreenX', sx), ('StartScreenY', sy), ('EndScreenX', ex), ('EndScreenY', ey)):
        H.pin(key, pin_name, 'real', 'float', default='0.0'); H.link((src, 'ReturnValue'), (key, pin_name))
    H.pin(key, 'LineColor', 'struct', obj=STR('/Script/CoreUObject.LinearColor'), default='(R=1.000000,G=1.000000,B=1.000000,A=0.900000)')
    H.pin(key, 'LineThickness', 'real', 'float', default='2.000000')
line('LineH', 'XL', 'CY', 'XR', 'CY', 950); line('LineV', 'CX', 'YT', 'CX', 'YB', 1250)
chain(H, 'Draw', 'LineH', 'LineV')
open(OUT_HUD, 'w', encoding='utf-8', newline='\r\n').write(H.text())
print('ok', len(C.order), len(H.order))
