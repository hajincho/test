"""Node text for right-mouse aiming. usage: gen_fp_aim_t3d.py <Data>  -> fp_aim_abp.t3d, fp_aim_char.t3d, fp_aim_hud.t3d
ABP (AnimGraph): ModifyCurve AimADS / AimShoulder = FindComponentByTag(pawn, 'FurinaADS' / 'FurinaShoulder').IsActive
Character: tap -> toggle ADS (entering from third person sets FurinaFPWanted and remembers to restore it; FOV 85 -> 60),
           hold -> FurinaShoulder active + face the aim; release -> rotation settings follow the current view.
HUD: ADS -> no crosshair at all (the iron sight is the aiming point); otherwise the cross.
ABP (second paste): ModifyCurve_ViewState 'ViewTP' = not FindComponentByTag('FurinaFPCamera').IsActive -> fp_view_abp.t3d"""
import sys
D = sys.argv[1]
src = open(__file__.replace('gen_fp_aim_t3d.py', 'gen_fp_view_t3d.py'), encoding='utf-8').read()
sys.argv = ['x', 'unused']; ns = {}; exec(src.split('G = Graph()')[0], ns)
Graph, CLS, STR, ENUM, E = ns['Graph'], ns['CLS'], ns['STR'], ns['ENUM'], ns['E']
POSE = "/Script/CoreUObject.ScriptStruct'/Script/Engine.PoseLink'"

def helpers(G, prefix):
    def call(key, owner, func, x, y, pure=False, self_cls=None, self_link=None):
        props = ['FunctionReference=(MemberParent="%s",MemberName="%s")' % (CLS(owner), func)]
        if pure: props.insert(0, 'bIsPureFunc=True')
        G.node(key, '/Script/BlueprintGraph.K2Node_CallFunction', props, x, y)
        if not pure: G.pin(key, 'execute', 'exec'); G.pin(key, 'then', 'exec', out=True)
        if self_cls:
            G.pin(key, 'self', 'object', obj=CLS(self_cls))
            if self_link: G.link(self_link, (key, 'self'))
        return key
    def find_flag(key, pawn_ref, tag, x, y):     # FindComponentByTag(...).IsActive -> bool ref
        call(key + 'F', E + 'Actor', 'FindComponentByTag', x, y, pure=True, self_cls=E + 'Actor', self_link=pawn_ref)
        G.pin(key + 'F', 'ComponentClass', 'class', obj=CLS(E + 'ActorComponent'), default=None)
        G.find((key + 'F', 'ComponentClass'))['default'] = None
        G.nodes[key + 'F']['pins'][-1]['default_object'] = None
        G.pin(key + 'F', 'Tag', 'name', default=tag)
        G.pin(key + 'F', 'ReturnValue', 'object', obj=CLS(E + 'ActorComponent'), out=True)
        call(key, E + 'ActorComponent', 'IsActive', x + 300, y, pure=True, self_cls=E + 'ActorComponent', self_link=(key + 'F', 'ReturnValue'))
        G.pin(key, 'ReturnValue', 'bool', out=True)
        return (key, 'ReturnValue')
    return call, find_flag

def text_with_default_objects(G, replace):
    t = G.text().replace('K2Node_FPV_', replace)
    # FindComponentByTag class pin default (ActorComponent) - Graph has no DefaultObject field, add it textually
    return t.replace('PinName="ComponentClass",', 'PinName="ComponentClass",').replace(
        'PinType.PinCategory="class",PinType.PinSubCategory="",PinType.PinSubCategoryObject="%s",' % CLS(E + 'ActorComponent'),
        'PinType.PinCategory="class",PinType.PinSubCategory="",PinType.PinSubCategoryObject="%s",' % CLS(E + 'ActorComponent'))

# ======================= ABP
A = Graph(); call, find_flag = helpers(A, 'A')
call('Owner', E + 'AnimInstance', 'TryGetPawnOwner', 0, 0, pure=True, self_cls=E + 'AnimInstance')
own = A.pin('Owner', 'ReturnValue', 'object', obj=CLS(E + 'Pawn'), out=True)
vals = []
for i, (tag, y) in enumerate((('FurinaADS', 0), ('FurinaShoulder', 300))):
    flag = find_flag('Flag%d' % i, own, tag, 300, y)
    call('ToF%d' % i, E + 'KismetMathLibrary', 'Conv_BoolToDouble', 900, y, pure=True)
    A.pin('ToF%d' % i, 'InBool', 'bool', default='false'); A.link(flag, ('ToF%d' % i, 'InBool'))
    A.pin('ToF%d' % i, 'ReturnValue', 'real', 'double', out=True); vals.append(('ToF%d' % i, 'ReturnValue'))
A.node('MC', '/Script/AnimGraph.AnimGraphNode_ModifyCurve', ['Node=(CurveValues=(0.000000,0.000000),CurveNames=("AimADS","AimShoulder"),Alpha=1.000000,ApplyMode=Blend)'], 1200, -300)
A.nodes['MC']['name'] = 'AnimGraphNode_ModifyCurve_AimState'
A.pin('MC', 'SourcePose', 'struct', obj=POSE, default='(LinkID=-1,SourceLinkID=-1)')
A.pin('MC', 'Pose', 'struct', obj=POSE, out=True)
for i, v in enumerate(vals):
    A.pin('MC', 'CurveValues_%d' % i, 'real', 'float', default='0.0'); A.link(v, ('MC', 'CurveValues_%d' % i))
open(D + r'\fp_aim_abp.t3d', 'w', encoding='utf-8', newline='\r\n').write(A.text().replace('K2Node_FPV_', 'K2Node_FPAA_'))

# ======================= Character
C = Graph(); call, _ = helpers(C, 'C')
def var_get(key, member, cls, x, y):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member], x, y)
    return C.pin(key, member, 'object', obj=CLS(cls), out=True)
def eia(key, ia, x, y):
    C.node(key, '/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', ["InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/%s.%s'\"" % (ia, ia)], x, y)
    for p in ('Triggered', 'Started', 'Ongoing', 'Canceled', 'Completed'): C.pin(key, p, 'exec', out=True)
    C.pin(key, 'ActionValue', 'bool', out=True, default='false')
def is_active(key, comp_ref, x, y):
    call(key, E + 'ActorComponent', 'IsActive', x, y, pure=True, self_cls=E + 'ActorComponent', self_link=comp_ref)
    C.pin(key, 'ReturnValue', 'bool', out=True); return (key, 'ReturnValue')
def set_active(key, comp_ref, on, x, y):
    call(key, E + 'ActorComponent', 'SetActive', x, y, self_cls=E + 'ActorComponent', self_link=comp_ref)
    C.pin(key, 'bNewActive', 'bool', default='true' if on else 'false'); C.pin(key, 'bReset', 'bool', default='false')
def branch(key, cond, x, y):
    C.node(key, '/Script/BlueprintGraph.K2Node_IfThenElse', [], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'Condition', 'bool', default='true'); C.pin(key, 'then', 'exec', out=True); C.pin(key, 'else', 'exec', out=True)
    C.link(cond, (key, 'Condition'))
def fov(key, cam_ref, v, x, y):
    call(key, E + 'CameraComponent', 'SetFieldOfView', x, y, self_cls=E + 'CameraComponent', self_link=cam_ref)
    C.pin(key, 'InFieldOfView', 'real', 'float', default='%f' % v)
SC = E + 'SceneComponent'
X, Y = -2600, 26000
eia('AdsIA', 'IA_FurinaADS', X, Y)
ads = var_get('GetAds', 'FurinaADS', SC, X + 100, Y + 250)
want = var_get('GetWant', 'FurinaFPWanted', SC, X + 100, Y + 350)
rest = var_get('GetRestore', 'FurinaADSRestoreTP', SC, X + 100, Y + 450)
cam = var_get('GetCam', 'FPCamera', E + 'CameraComponent', X + 100, Y + 550)
call('AdsToggle', E + 'ActorComponent', 'ToggleActive', X + 350, Y, self_cls=E + 'ActorComponent', self_link=ads)
C.link(('AdsIA', 'Triggered'), ('AdsToggle', 'execute'))
branch('AdsOn', is_active('AdsIsOn', ads, X + 400, Y + 250), X + 650, Y); C.link(('AdsToggle', 'then'), ('AdsOn', 'execute'))
# entering ADS
branch('WasFP', is_active('WantIsOn', want, X + 700, Y + 300), X + 950, Y - 200); C.link(('AdsOn', 'then'), ('WasFP', 'execute'))
set_active('ForceFP', want, True, X + 1250, Y - 100); set_active('MarkRestore', rest, True, X + 1550, Y - 100)
C.link(('WasFP', 'else'), ('ForceFP', 'execute')); C.link(('ForceFP', 'then'), ('MarkRestore', 'execute'))
fov('Fov60', cam, 60.0, X + 1850, Y - 200); C.link(('WasFP', 'then'), ('Fov60', 'execute')); C.link(('MarkRestore', 'then'), ('Fov60', 'execute'))
# leaving ADS
branch('NeedRestore', is_active('RestoreIsOn', rest, X + 700, Y + 450), X + 950, Y + 200); C.link(('AdsOn', 'else'), ('NeedRestore', 'execute'))
set_active('BackTP', want, False, X + 1250, Y + 300); set_active('ClearRestore', rest, False, X + 1550, Y + 300)
C.link(('NeedRestore', 'then'), ('BackTP', 'execute')); C.link(('BackTP', 'then'), ('ClearRestore', 'execute'))
fov('Fov85', cam, 85.0, X + 1850, Y + 200); C.link(('NeedRestore', 'else'), ('Fov85', 'execute')); C.link(('ClearRestore', 'then'), ('Fov85', 'execute'))
# shoulder hold
SY = Y + 900
eia('ShIA', 'IA_FurinaShoulder', X, SY)
sh = var_get('GetSh', 'FurinaShoulder', SC, X + 100, SY + 250)
cmc = var_get('GetCMC', 'CharacterMovement', E + 'CharacterMovementComponent', X + 100, SY + 350)
cam2 = var_get('GetCam2', 'FPCamera', E + 'CameraComponent', X + 100, SY + 450)
def yaw(key, x, y, value=None, link=None):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberName="bUseControllerRotationYaw",bSelfContext=True)'], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'then', 'exec', out=True); C.pin(key, 'bUseControllerRotationYaw', 'bool', default=value or 'false')
    if link: C.link(link, (key, 'bUseControllerRotationYaw'))
def orient(key, x, y, value=None, link=None):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="bOrientRotationToMovement")' % CLS(E + 'CharacterMovementComponent'), 'SelfContextInfo=NotSelfContext'], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'then', 'exec', out=True); C.pin(key, 'bOrientRotationToMovement', 'bool', default=value or 'false')
    C.pin(key, 'self', 'object', obj=CLS(E + 'CharacterMovementComponent')); C.link(cmc, (key, 'self'))
    if link: C.link(link, (key, 'bOrientRotationToMovement'))
set_active('ShOn', sh, True, X + 400, SY - 150); yaw('ShYawOn', X + 700, SY - 150, 'true'); orient('ShOrientOff', X + 1000, SY - 150, 'false')
C.link(('ShIA', 'Triggered'), ('ShOn', 'execute')); C.link(('ShOn', 'then'), ('ShYawOn', 'execute')); C.link(('ShYawOn', 'then'), ('ShOrientOff', 'execute'))
fp_now = is_active('CamIsOn', cam2, X + 400, SY + 450)
call('NotFP', E + 'KismetMathLibrary', 'Not_PreBool', X + 650, SY + 450, pure=True)
C.pin('NotFP', 'A', 'bool', default='false'); C.link(fp_now, ('NotFP', 'A')); C.pin('NotFP', 'ReturnValue', 'bool', out=True)
set_active('ShOff', sh, False, X + 400, SY + 150); yaw('ShYawBack', X + 700, SY + 150, link=fp_now); orient('ShOrientBack', X + 1000, SY + 150, link=('NotFP', 'ReturnValue'))
C.link(('ShIA', 'Completed'), ('ShOff', 'execute')); C.link(('ShIA', 'Canceled'), ('ShOff', 'execute'))
C.link(('ShOff', 'then'), ('ShYawBack', 'execute')); C.link(('ShYawBack', 'then'), ('ShOrientBack', 'execute'))
open(D + r'\fp_aim_char.t3d', 'w', encoding='utf-8', newline='\r\n').write(C.text().replace('K2Node_FPV_', 'K2Node_FPAC_'))

# ======================= HUD
H = Graph(); call, find_flag = helpers(H, 'H')
H.node('Draw', '/Script/BlueprintGraph.K2Node_Event', ['EventReference=(MemberParent="%s",MemberName="ReceiveDrawHUD")' % CLS(E + 'HUD'), 'bOverrideFunction=True'], 0, 0)
H.pin('Draw', 'OutputDelegate', 'delegate', out=True, hidden=True); H.pin('Draw', 'then', 'exec', out=True)
H.pin('Draw', 'SizeX', 'int', out=True); H.pin('Draw', 'SizeY', 'int', out=True)
call('Pawn', E + 'HUD', 'GetOwningPawn', 0, 600, pure=True, self_cls=E + 'HUD')
H.pin('Pawn', 'ReturnValue', 'object', obj=CLS(E + 'Pawn'), out=True)
ads_flag = find_flag('AdsF', ('Pawn', 'ReturnValue'), 'FurinaADS', 250, 600)
H.node('IsAds', '/Script/BlueprintGraph.K2Node_IfThenElse', [], 900, 0)
H.pin('IsAds', 'execute', 'exec'); H.pin('IsAds', 'Condition', 'bool', default='false'); H.pin('IsAds', 'then', 'exec', out=True); H.pin('IsAds', 'else', 'exec', out=True)
H.link(('Draw', 'then'), ('IsAds', 'execute')); H.link(ads_flag, ('IsAds', 'Condition'))
def half(key, src_pin, x, y):
    call(key + 'D', E + 'KismetMathLibrary', 'Conv_IntToDouble', x, y, pure=True)
    H.pin(key + 'D', 'InInt', 'int', default='0'); H.link(('Draw', src_pin), (key + 'D', 'InInt')); H.pin(key + 'D', 'ReturnValue', 'real', 'double', out=True)
    call(key, E + 'KismetMathLibrary', 'Multiply_DoubleDouble', x + 250, y, pure=True)
    H.pin(key, 'A', 'real', 'double', default='0.0'); H.link((key + 'D', 'ReturnValue'), (key, 'A'))
    H.pin(key, 'B', 'real', 'double', default='0.5'); H.pin(key, 'ReturnValue', 'real', 'double', out=True)
def offs(key, src, d, x, y):
    call(key, E + 'KismetMathLibrary', 'Add_DoubleDouble', x, y, pure=True)
    H.pin(key, 'A', 'real', 'double', default='0.0'); H.link((src, 'ReturnValue'), (key, 'A'))
    H.pin(key, 'B', 'real', 'double', default='%f' % d); H.pin(key, 'ReturnValue', 'real', 'double', out=True)
half('CX', 'SizeX', 0, 300); half('CY', 'SizeY', 0, 450)
offs('XL', 'CX', -11, 600, 250); offs('XR', 'CX', 11, 600, 350); offs('YT', 'CY', -11, 600, 450); offs('YB', 'CY', 11, 600, 550)
def line(key, sx, sy, ex, ey, x):
    call(key, E + 'HUD', 'DrawLine', x, 150, self_cls=None)
    for pin_name, s in (('StartScreenX', sx), ('StartScreenY', sy), ('EndScreenX', ex), ('EndScreenY', ey)):
        H.pin(key, pin_name, 'real', 'float', default='0.0'); H.link((s, 'ReturnValue'), (key, pin_name))
    H.pin(key, 'LineColor', 'struct', obj=STR('/Script/CoreUObject.LinearColor'), default='(R=1.000000,G=1.000000,B=1.000000,A=0.900000)')
    H.pin(key, 'LineThickness', 'real', 'float', default='2.000000')
line('LineH', 'XL', 'CY', 'XR', 'CY', 1200); line('LineV', 'CX', 'YT', 'CX', 'YB', 1500)
H.link(('IsAds', 'else'), ('LineH', 'execute')); H.link(('LineH', 'then'), ('LineV', 'execute'))
# ADS: nothing is drawn - the iron sight is the aiming point (IsAds.then left unconnected)
open(D + r'\fp_aim_hud.t3d', 'w', encoding='utf-8', newline='\r\n').write(H.text().replace('K2Node_FPV_', 'K2Node_FPAH_'))
print('ok', len(A.order), len(C.order), len(H.order))

# ======================= ABP: ViewTP curve (third person = FPCamera, tagged 'FurinaFPCamera', not active)
V = Graph(); call, find_flag = helpers(V, 'V')
call('Owner', E + 'AnimInstance', 'TryGetPawnOwner', 0, 0, pure=True, self_cls=E + 'AnimInstance')
own = V.pin('Owner', 'ReturnValue', 'object', obj=CLS(E + 'Pawn'), out=True)
fp = find_flag('FPOn', own, 'FurinaFPCamera', 300, 0)
call('NotFP', E + 'KismetMathLibrary', 'Not_PreBool', 900, 0, pure=True)
V.pin('NotFP', 'A', 'bool', default='false'); V.link(fp, ('NotFP', 'A')); V.pin('NotFP', 'ReturnValue', 'bool', out=True)
call('ToF', E + 'KismetMathLibrary', 'Conv_BoolToDouble', 1100, 0, pure=True)
V.pin('ToF', 'InBool', 'bool', default='false'); V.link(('NotFP', 'ReturnValue'), ('ToF', 'InBool'))
V.pin('ToF', 'ReturnValue', 'real', 'double', out=True)
V.node('MC', '/Script/AnimGraph.AnimGraphNode_ModifyCurve', ['Node=(CurveValues=(0.000000),CurveNames=("ViewTP"),Alpha=1.000000,ApplyMode=Blend)'], 1400, -300)
V.nodes['MC']['name'] = 'AnimGraphNode_ModifyCurve_ViewState'
V.pin('MC', 'SourcePose', 'struct', obj=POSE, default='(LinkID=-1,SourceLinkID=-1)')
V.pin('MC', 'Pose', 'struct', obj=POSE, out=True)
V.pin('MC', 'CurveValues_0', 'real', 'float', default='0.0'); V.link(('ToF', 'ReturnValue'), ('MC', 'CurveValues_0'))
open(D + r'\fp_view_abp.t3d', 'w', encoding='utf-8', newline='\r\n').write(V.text().replace('K2Node_FPV_', 'K2Node_FPVW_'))
print('view curve ok', len(V.order))

# ======================= ABP: Crouch curve (flag component 'FurinaCrouch', set by the character's Event Tick from IsCrouching)
K = Graph(); call, find_flag = helpers(K, 'K')
call('Owner', E + 'AnimInstance', 'TryGetPawnOwner', 0, 0, pure=True, self_cls=E + 'AnimInstance')
own = K.pin('Owner', 'ReturnValue', 'object', obj=CLS(E + 'Pawn'), out=True)
cr_flag = find_flag('CrOn', own, 'FurinaCrouch', 300, 0)
call('ToF', E + 'KismetMathLibrary', 'Conv_BoolToDouble', 900, 0, pure=True)
K.pin('ToF', 'InBool', 'bool', default='false'); K.link(cr_flag, ('ToF', 'InBool'))
K.pin('ToF', 'ReturnValue', 'real', 'double', out=True)
K.node('MC', '/Script/AnimGraph.AnimGraphNode_ModifyCurve', ['Node=(CurveValues=(0.000000),CurveNames=("Crouch"),Alpha=1.000000,ApplyMode=Blend)'], 1200, -300)
K.nodes['MC']['name'] = 'AnimGraphNode_ModifyCurve_CrouchState'
K.pin('MC', 'SourcePose', 'struct', obj=POSE, default='(LinkID=-1,SourceLinkID=-1)')
K.pin('MC', 'Pose', 'struct', obj=POSE, out=True)
K.pin('MC', 'CurveValues_0', 'real', 'float', default='0.0'); K.link(('ToF', 'ReturnValue'), ('MC', 'CurveValues_0'))
open(D + r'\fp_crouch_abp.t3d', 'w', encoding='utf-8', newline='\r\n').write(K.text().replace('K2Node_FPV_', 'K2Node_FPCR_'))
print('crouch curve ok', len(K.order))
