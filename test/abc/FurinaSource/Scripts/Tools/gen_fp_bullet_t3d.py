"""Node text for tracer rounds. usage: gen_fp_bullet_t3d.py <Data> -> fp_bullet_bp.t3d (BP_FurinaBullet), fp_fire_char.t3d (character)
BP_FurinaBullet:
  BeginPlay -> Bullet.IgnoreActorWhenMoving(Instigator)
  Tick      -> air drag  Ballistics.Velocity *= 1 - k*|v|*dt  (k from Data/ballistics.json, quadratic drag)
            -> Tracer streak from 1.5 m past the muzzle to the round, max 25 m long, width 1 cm + 0.2 % of the distance
  Hit       -> debug sphere at the impact (5 s) -> physics bodies get an impulse along the flight -> destroy
Character:
  IA_FurinaFireRifle Started -> SetTimer('FurinaRifleShot', 60/rpm, looping, first shot next frame); Completed/Canceled -> ClearTimer
  (those IA / timer nodes already live in the BP; this file now only regenerates the FurinaRifleShot event body)
  FurinaRifleShot: sprinting -> shoulder stance, no shot; hip + moving -> no shot; otherwise: face the aim yaw -> fire montage + rifle fire anim -> camera trace (500 m) -> aim point ->
     muzzle (rifle mesh (0, 48.5, 3.1)) -> direction to the aim point + 100 m zero elevation (camera up) ->
     random cone (base x stance multiplier + speed penalty) -> spawn BP_FurinaBullet (instigator = self)
     -> recoil: control rotation += random vertical / horizontal kick x stance multiplier (hip 1.10, shoulder 1.05, ADS 0.90)"""
import sys, json
D = sys.argv[1]
src = open(__file__.replace('gen_fp_bullet_t3d.py', 'gen_fp_bp_t3d.py'), encoding='utf-8').read().split('# ======================= character graph')[0]
sys.argv = ['x', 'a', 'b']; ns = {}; exec(src, ns)
Graph, CLS, STR, ENUM, E, call0 = ns['Graph'], ns['CLS'], ns['STR'], ns['ENUM'], ns['E'], ns['call']
B = json.load(open(D + r'\ballistics.json'))
VEC, ROT, XF = STR('/Script/CoreUObject.Vector'), STR('/Script/CoreUObject.Rotator'), STR('/Script/CoreUObject.Transform')
KML, KSL = E + 'KismetMathLibrary', E + 'KismetSystemLibrary'
BULLET_C = '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'

def kit(G):
    def call(*a, **k): return call0(G, *a, **k)
    def event(key, func, owner, x, y, outs=()):
        G.node(key, '/Script/BlueprintGraph.K2Node_Event', ['EventReference=(MemberParent="%s",MemberName="%s")' % (CLS(E + owner), func), 'bOverrideFunction=True'], x, y)
        G.pin(key, 'OutputDelegate', 'delegate', out=True, hidden=True); G.pin(key, 'then', 'exec', out=True)
        for o in outs: G.pin(key, o[0], o[1], o[2] if len(o) > 2 else '', obj=o[3] if len(o) > 3 else None, out=True)
    def pure(key, owner, func, x, y, ins=(), out=None, self_cls=None, self_link=None):
        call(key, owner, func, x, y, pure=True, self_cls=self_cls, self_link=self_link)
        for name, cat, sub, obj, src, default in ins:
            G.pin(key, name, cat, sub, obj=obj, default=default)
            if src: G.link(src, (key, name))
        if out: G.pin(key, 'ReturnValue', out[0], out[1] if len(out) > 1 else '', obj=out[2] if len(out) > 2 else None, out=True)
        return (key, 'ReturnValue')
    def var(key, member, cls, x, y):
        G.node(key, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberName="%s",bSelfContext=True)' % member], x, y)
        return G.pin(key, member, 'object', obj=CLS(cls), out=True)
    def branch(key, cond, x, y):
        G.node(key, '/Script/BlueprintGraph.K2Node_IfThenElse', [], x, y)
        G.pin(key, 'execute', 'exec'); G.pin(key, 'Condition', 'bool', default='true'); G.pin(key, 'then', 'exec', out=True); G.pin(key, 'else', 'exec', out=True)
        G.link(cond, (key, 'Condition'))
    def comp_var(key, member, owner, x, y, self_ref):      # property of another object (PMC.Velocity)
        G.node(key, '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberParent="%s",MemberName="%s")' % (CLS(owner), member), 'SelfContextInfo=NotSelfContext'], x, y)
        G.pin(key, member, 'struct', obj=VEC, out=True); G.pin(key, 'self', 'object', obj=CLS(owner)); G.link(self_ref, (key, 'self'))
        return (key, member)
    return call, event, pure, var, branch, comp_var
def vin(name, src): return (name, 'struct', '', VEC, src, None)
def fin(name, src, d='0.0', sub='double'): return (name, 'real', sub, None, src, d)

# ======================= bullet actor
A = Graph(); call, event, pure, var, branch, comp_var = kit(A)
PMC = E + 'ProjectileMovementComponent'
event('Begin', 'ReceiveBeginPlay', 'Actor', 0, 0)
inst = pure('Inst', E + 'Actor', 'GetInstigator', 0, 200, out=('object', '', CLS(E + 'Pawn')), self_cls=E + 'Actor')
sph = var('GetSph', 'Bullet', E + 'SphereComponent', 0, 320)
call('Ignore', E + 'PrimitiveComponent', 'IgnoreActorWhenMoving', 350, 0, self_cls=E + 'PrimitiveComponent', self_link=sph)
A.pin('Ignore', 'Actor', 'object', obj=CLS(E + 'Actor')); A.link(inst, ('Ignore', 'Actor')); A.pin('Ignore', 'bShouldIgnore', 'bool', default='true')
A.link(('Begin', 'then'), ('Ignore', 'execute'))
# tick: quadratic air drag
TY = 600
event('Tick', 'ReceiveTick', 'Actor', 0, TY, outs=[('DeltaSeconds', 'real', 'float')])
pm = var('GetPM', 'Ballistics', PMC, 0, TY + 250)
vel = comp_var('Vel', 'Velocity', PMC, 250, TY + 250, pm)
spd = pure('Spd', KML, 'VSize', 500, TY + 350, ins=[vin('A', vel)], out=('real', 'double'))
kdt = pure('Kdt', KML, 'Multiply_DoubleDouble', 750, TY + 350, ins=[fin('A', spd), fin('B', ('Tick', 'DeltaSeconds'))], out=('real', 'double'))
kv = pure('Kv', KML, 'Multiply_DoubleDouble', 1000, TY + 350, ins=[fin('A', kdt), fin('B', None, '%.9g' % B['k_per_cm'])], out=('real', 'double'))
fac = pure('Fac', KML, 'Subtract_DoubleDouble', 1250, TY + 350, ins=[fin('A', None, '1.0'), fin('B', kv)], out=('real', 'double'))
nv = pure('NewVel', KML, 'Multiply_VectorFloat', 1500, TY + 250, ins=[vin('A', vel), fin('B', fac)], out=('struct', '', VEC))
A.node('SetVel', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="Velocity")' % CLS(PMC), 'SelfContextInfo=NotSelfContext'], 1750, TY)
A.pin('SetVel', 'execute', 'exec'); A.pin('SetVel', 'then', 'exec', out=True)
A.pin('SetVel', 'Velocity', 'struct', obj=VEC); A.link(nv, ('SetVel', 'Velocity'))
A.pin('SetVel', 'self', 'object', obj=CLS(PMC)); A.link(pm, ('SetVel', 'self'))
A.pin('SetVel', 'Output_Get', 'struct', obj=VEC, out=True)
A.link(('Tick', 'then'), ('SetVel', 'execute'))
age = pure('Age', E + 'Actor', 'GetGameTimeSinceCreation', 1750, TY + 400, out=('real', 'double'), self_cls=E + 'Actor')
# tracer streak: from 1.5 m past the muzzle to the round (distance flown = v0 * age), at most 25 m (the eye's persistence of the
# burning tracer); width 1 cm + 0.2 % of the distance
# (keeps a few pixels wide far away while staying thin next to the camera)
flown = pure('Flown', KML, 'Multiply_DoubleDouble', 2000, TY + 400, ins=[fin('A', age), fin('B', None, '%d' % B['muzzle_cms'])], out=('real', 'double'))
past = pure('Past', KML, 'Subtract_DoubleDouble', 2250, TY + 300, ins=[fin('A', flown), fin('B', None, '150.0')], out=('real', 'double'))
ln0 = pure('Len0', KML, 'FMin', 2250, TY + 400, ins=[fin('A', past), fin('B', None, '2500.0')], out=('real', 'double'))
ln = pure('Len', KML, 'FMax', 2400, TY + 400, ins=[fin('A', ln0), fin('B', None, '0.0')], out=('real', 'double'))
lz = pure('LenS', KML, 'Multiply_DoubleDouble', 2500, TY + 400, ins=[fin('A', ln), fin('B', None, '0.01')], out=('real', 'double'))
wd = pure('Wid', KML, 'Multiply_DoubleDouble', 2250, TY + 550, ins=[fin('A', flown), fin('B', None, '0.00002')], out=('real', 'double'))
ws = pure('WidS', KML, 'Add_DoubleDouble', 2500, TY + 550, ins=[fin('A', wd), fin('B', None, '0.01')], out=('real', 'double'))
ws2 = pure('WidC', KML, 'FMin', 2750, TY + 550, ins=[fin('A', ws), fin('B', None, '0.3')], out=('real', 'double'))
sc = pure('Scale', KML, 'MakeVector', 3000, TY + 400, ins=[fin('X', ws2), fin('Y', ws2), fin('Z', lz)], out=('struct', '', VEC))
back = pure('Back', KML, 'Multiply_DoubleDouble', 2750, TY + 700, ins=[fin('A', ln), fin('B', None, '-0.5')], out=('real', 'double'))
loc = pure('Loc', KML, 'MakeVector', 3000, TY + 700, ins=[fin('X', back), fin('Y', None, '0.0'), fin('Z', None, '0.0')], out=('struct', '', VEC))
tr = var('GetTr', 'Tracer', E + 'StaticMeshComponent', 2000, TY + 250)
call('Grow', E + 'SceneComponent', 'SetRelativeScale3D', 2300, TY, self_cls=E + 'SceneComponent', self_link=tr)
A.pin('Grow', 'NewScale3D', 'struct', obj=VEC); A.link(sc, ('Grow', 'NewScale3D'))
A.link(('SetVel', 'then'), ('Grow', 'execute'))
call('Trail', E + 'SceneComponent', 'K2_SetRelativeLocation', 2700, TY, self_cls=E + 'SceneComponent', self_link=tr)
A.pin('Trail', 'NewLocation', 'struct', obj=VEC); A.link(loc, ('Trail', 'NewLocation'))
A.pin('Trail', 'bSweep', 'bool', default='false'); A.pin('Trail', 'SweepHitResult', 'struct', obj=STR(E + 'HitResult'), out=True)
A.pin('Trail', 'bTeleport', 'bool', default='true')
A.link(('Grow', 'then'), ('Trail', 'execute'))
# hit
HY = 1300
event('Hit', 'ReceiveHit', 'Actor', 0, HY, outs=[('MyComp', 'object', '', CLS(E + 'PrimitiveComponent')), ('Other', 'object', '', CLS(E + 'Actor')),
      ('OtherComp', 'object', '', CLS(E + 'PrimitiveComponent')), ('bSelfMoved', 'bool'), ('HitLocation', 'struct', '', VEC),
      ('HitNormal', 'struct', '', VEC), ('NormalImpulse', 'struct', '', VEC), ('Hit', 'struct', '', STR(E + 'HitResult'))])
call('Mark', KSL, 'DrawDebugSphere', 400, HY)
A.pin('Mark', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
A.pin('Mark', 'Center', 'struct', obj=VEC); A.link(('Hit', 'HitLocation'), ('Mark', 'Center'))
A.pin('Mark', 'Radius', 'real', 'float', default='5.000000'); A.pin('Mark', 'Segments', 'int', default='8')
A.pin('Mark', 'LineColor', 'struct', obj=STR('/Script/CoreUObject.LinearColor'), default='(R=1.000000,G=0.850000,B=0.100000,A=1.000000)')
A.pin('Mark', 'Duration', 'real', 'float', default='5.000000'); A.pin('Mark', 'Thickness', 'real', 'float', default='1.000000')
A.link(('Hit', 'then'), ('Mark', 'execute'))
sim = pure('IsSim', E + 'PrimitiveComponent', 'IsSimulatingPhysics', 400, HY + 300, ins=[('BoneName', 'name', '', None, None, 'None')], out=('bool',),
           self_cls=E + 'PrimitiveComponent', self_link=('Hit', 'OtherComp'))
branch('SimB', sim, 750, HY); A.link(('Mark', 'then'), ('SimB', 'execute'))
pm2 = var('GetPM2', 'Ballistics', PMC, 500, HY + 450)
vel2 = comp_var('Vel2', 'Velocity', PMC, 750, HY + 450, pm2)
nd = pure('Dir', KML, 'Normal', 1000, HY + 450, ins=[vin('A', vel2), ('Tolerance', 'real', 'float', None, None, '0.000100')], out=('struct', '', VEC))
imp = pure('Imp', KML, 'Multiply_VectorFloat', 1250, HY + 450, ins=[vin('A', nd), fin('B', None, '30000.0')], out=('struct', '', VEC))
call('Push', E + 'PrimitiveComponent', 'AddImpulseAtLocation', 1100, HY, self_cls=E + 'PrimitiveComponent', self_link=('Hit', 'OtherComp'))
A.pin('Push', 'Impulse', 'struct', obj=VEC); A.link(imp, ('Push', 'Impulse'))
A.pin('Push', 'Location', 'struct', obj=VEC); A.link(('Hit', 'HitLocation'), ('Push', 'Location')); A.pin('Push', 'BoneName', 'name', default='None')
A.link(('SimB', 'then'), ('Push', 'execute'))
call('Kill', E + 'Actor', 'K2_DestroyActor', 1450, HY, self_cls=E + 'Actor')
A.link(('Push', 'then'), ('Kill', 'execute')); A.link(('SimB', 'else'), ('Kill', 'execute'))
open(D + r'\fp_bullet_bp.t3d', 'w', encoding='utf-8', newline='\r\n').write(A.text().replace('K2Node_FP_', 'K2Node_FPB_'))

# ======================= character
C = Graph(); call, event, pure, var, branch, comp_var = kit(C)
X, Y = -2600, 29000
C.node('Self', '/Script/BlueprintGraph.K2Node_Self', [], X + 100, Y + 300); me = C.pin('Self', 'self', 'object', 'self', out=True)
# the shot
SY = Y + 800
C.node('Shot', '/Script/BlueprintGraph.K2Node_CustomEvent', ['CustomFunctionName="FurinaRifleShot"'], X, SY)
C.pin('Shot', 'OutputDelegate', 'delegate', out=True, hidden=True); C.pin('Shot', 'then', 'exec', out=True)
ctrl = pure('CtrlRot', E + 'Pawn', 'GetControlRotation', X, SY + 250, out=('struct', '', ROT), self_cls=E + 'Pawn')
call('BreakCtrl', KML, 'BreakRotator', X + 250, SY + 250, pure=True)
C.pin('BreakCtrl', 'InRot', 'struct', obj=ROT); C.link(ctrl, ('BreakCtrl', 'InRot'))
for n in ('Roll', 'Pitch', 'Yaw'): C.pin('BreakCtrl', n, 'real', 'float', out=True)
call('MakeYaw', KML, 'MakeRotator', X + 500, SY + 250, pure=True)
C.pin('MakeYaw', 'Roll', 'real', 'float', default='0.0'); C.pin('MakeYaw', 'Pitch', 'real', 'float', default='0.0')
C.pin('MakeYaw', 'Yaw', 'real', 'float', default='0.0'); C.link(('BreakCtrl', 'Yaw'), ('MakeYaw', 'Yaw'))
C.pin('MakeYaw', 'ReturnValue', 'struct', obj=ROT, out=True)
call('FaceAim', E + 'Actor', 'K2_SetActorRotation', X + 300, SY, self_cls=E + 'Actor')
C.pin('FaceAim', 'NewRotation', 'struct', obj=ROT); C.link(('MakeYaw', 'ReturnValue'), ('FaceAim', 'NewRotation'))
C.pin('FaceAim', 'bTeleportPhysics', 'bool', default='false'); C.pin('FaceAim', 'ReturnValue', 'bool', out=True)
# (Shot -> rules -> FaceAim link is made at the end)
mesh = var('GetMeshF', 'FurinaMesh', E + 'SkeletalMeshComponent', X + 500, SY + 450)
ai = pure('AnimInstF', E + 'SkeletalMeshComponent', 'GetAnimInstance', X + 650, SY + 450, out=('object', '', CLS(E + 'AnimInstance')),
          self_cls=E + 'SkeletalMeshComponent', self_link=mesh)
call('Kick', E + 'AnimInstance', 'Montage_Play', X + 650, SY, self_cls=E + 'AnimInstance', self_link=ai)
C.pin('Kick', 'MontageToPlay', 'object', obj=CLS(E + 'AnimMontage'), default_object='/Game/Furina/FP/Anim/AM_Furina_FP_Fire.AM_Furina_FP_Fire')
C.pin('Kick', 'InPlayRate', 'real', 'float', default='1.000000')
C.pin('Kick', 'ReturnValueType', 'byte', obj=ENUM(E + 'EMontagePlayReturnType'), default='MontageLength')
C.pin('Kick', 'InTimeToStartMontageAt', 'real', 'float', default='0.000000'); C.pin('Kick', 'bStopAllMontages', 'bool', default='true')
C.pin('Kick', 'ReturnValue', 'real', 'float', out=True)
C.link(('FaceAim', 'then'), ('Kick', 'execute'))
rifle = var('GetRifleF', 'FurinaRifle', E + 'SkeletalMeshComponent', X + 900, SY + 450)
call('Bolt', E + 'SkeletalMeshComponent', 'PlayAnimation', X + 1000, SY, self_cls=E + 'SkeletalMeshComponent', self_link=rifle)
C.pin('Bolt', 'NewAnimToPlay', 'object', obj=CLS(E + 'AnimationAsset'), default_object='/Game/Furina/FP/Weapon/A_FP_WEP_AssaultRifle_Fire.A_FP_WEP_AssaultRifle_Fire')
C.pin('Bolt', 'bLooping', 'bool', default='false')
C.link(('Kick', 'then'), ('Bolt', 'execute'))
# camera aim point
cm = pure('CamMgr', E + 'GameplayStatics', 'GetPlayerCameraManager', X + 900, SY + 650, out=('object', '', CLS(E + 'PlayerCameraManager')))
C.pin('CamMgr', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True); C.pin('CamMgr', 'PlayerIndex', 'int', default='0')
cl = pure('CamLoc', E + 'PlayerCameraManager', 'GetCameraLocation', X + 1150, SY + 650, out=('struct', '', VEC), self_cls=E + 'PlayerCameraManager', self_link=cm)
cr = pure('CamRot', E + 'PlayerCameraManager', 'GetCameraRotation', X + 1150, SY + 780, out=('struct', '', ROT), self_cls=E + 'PlayerCameraManager', self_link=cm)
fwd = pure('CamFwd', KML, 'GetForwardVector', X + 1400, SY + 780, ins=[('InRot', 'struct', '', ROT, cr, None)], out=('struct', '', VEC))
up = pure('CamUp', KML, 'GetUpVector', X + 1400, SY + 900, ins=[('InRot', 'struct', '', ROT, cr, None)], out=('struct', '', VEC))
# aim point: what the sight sees within 100 m, else the point 100 m down the sight line -> rounds cross the line of sight at
# 100 m (zero), rise ~3 cm above it at 50 m and drop below it past 100 m like a real 100 m zero
far = pure('Far', KML, 'Multiply_VectorFloat', X + 1650, SY + 780, ins=[vin('A', fwd), fin('B', None, '10000.0')], out=('struct', '', VEC))
end = pure('End', KML, 'Add_VectorVector', X + 1900, SY + 700, ins=[vin('A', cl), vin('B', far)], out=('struct', '', VEC))
call('Aim', KSL, 'LineTraceSingle', X + 1300, SY)
C.pin('Aim', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
C.pin('Aim', 'Start', 'struct', obj=VEC); C.link(cl, ('Aim', 'Start'))
C.pin('Aim', 'End', 'struct', obj=VEC); C.link(end, ('Aim', 'End'))
C.pin('Aim', 'TraceChannel', 'byte', obj=ENUM(E + 'ETraceTypeQuery'), default='TraceTypeQuery1')
C.pin('Aim', 'bTraceComplex', 'bool', default='false')
C.pin('Aim', 'ActorsToIgnore', 'object', obj=CLS(E + 'Actor'), container='Array')
C.pin('Aim', 'DrawDebugType', 'byte', obj=ENUM('/Script/Engine.EDrawDebugTrace'), default='None')
C.pin('Aim', 'OutHit', 'struct', obj=STR(E + 'HitResult'), out=True)
C.pin('Aim', 'bIgnoreSelf', 'bool', default='true')
C.pin('Aim', 'ReturnValue', 'bool', out=True)
C.link(('Bolt', 'then'), ('Aim', 'execute'))
call('BreakHit', E + 'GameplayStatics', 'BreakHitResult', X + 1650, SY + 250, pure=True)
C.pin('BreakHit', 'Hit', 'struct', obj=STR(E + 'HitResult')); C.link(('Aim', 'OutHit'), ('BreakHit', 'Hit'))
for name, cat, obj, sub in (('bBlockingHit', 'bool', None, ''), ('bInitialOverlap', 'bool', None, ''), ('Time', 'real', None, 'float'), ('Distance', 'real', None, 'float'),
                            ('Location', 'struct', VEC, ''), ('ImpactPoint', 'struct', VEC, ''), ('Normal', 'struct', VEC, ''), ('ImpactNormal', 'struct', VEC, ''),
                            ('PhysMat', 'object', CLS('/Script/PhysicsCore.PhysicalMaterial'), ''), ('HitActor', 'object', CLS(E + 'Actor'), ''),
                            ('HitComponent', 'object', CLS(E + 'PrimitiveComponent'), ''), ('HitBoneName', 'name', None, ''), ('BoneName', 'name', None, ''),
                            ('HitItem', 'int', None, ''), ('ElementIndex', 'int', None, ''), ('FaceIndex', 'int', None, ''),
                            ('TraceStart', 'struct', VEC, ''), ('TraceEnd', 'struct', VEC, '')):
    C.pin('BreakHit', name, cat, sub, obj=obj, out=True)
aimpt = pure('AimPt', KML, 'SelectVector', X + 2000, SY + 250, ins=[vin('A', ('BreakHit', 'ImpactPoint')), vin('B', end),
             ('bPickA', 'bool', '', None, ('Aim', 'ReturnValue'), 'false')], out=('struct', '', VEC))
ads_ref0 = var('GetAds0', 'FurinaADS', E + 'SceneComponent', X + 1650, SY + 1250)
ads_on0 = pure('AdsOn0', E + 'ActorComponent', 'IsActive', X + 1900, SY + 1250, out=('bool',), self_cls=E + 'ActorComponent', self_link=ads_ref0)
# 50 m point on the sight line (ADS)
p50 = pure('P50', KML, 'Multiply_VectorFloat', X + 2000, SY + 120, ins=[vin('A', fwd), fin('B', None, '5000.0')], out=('struct', '', VEC))
p50w = pure('P50W', KML, 'Add_VectorVector', X + 2250, SY + 120, ins=[vin('A', cl), vin('B', p50)], out=('struct', '', VEC))
# muzzle on the rifle mesh
rifle2 = var('GetRifleM', 'FurinaRifle', E + 'SkeletalMeshComponent', X + 1650, SY + 1050)
rx = pure('RifleXf', E + 'SceneComponent', 'K2_GetComponentToWorld', X + 1900, SY + 1050, out=('struct', '', XF), self_cls=E + 'SceneComponent', self_link=rifle2)
muz = pure('Muzzle', KML, 'TransformLocation', X + 2150, SY + 1050, ins=[('T', 'struct', '', XF, rx, None),
           ('Location', 'struct', '', VEC, None, '0.000000,40.625201,4.849452')], out=('struct', '', VEC))
aimsel = pure('AimSel', KML, 'SelectVector', X + 2300, SY + 330, ins=[vin('A', p50w), vin('B', aimpt), ('bPickA', 'bool', '', None, ads_on0, 'false')], out=('struct', '', VEC))
to = pure('ToAim', KML, 'Subtract_VectorVector', X + 2400, SY + 400, ins=[vin('A', aimsel), vin('B', muz)], out=('struct', '', VEC))
d0 = pure('Dir0', KML, 'Normal', X + 2650, SY + 400, ins=[vin('A', to), ('Tolerance', 'real', 'float', None, None, '0.000100')], out=('struct', '', VEC))
# ADS (iron sight, no crosshair): the bullet leaves the muzzle and crosses the sight line at 50 m - aim point = 50 m along the sight
# line (camera ray: in the ADS pose the aperture centre and the front post tip are on it), elevation for a 50 m zero. Hip / shoulder:
# crosshair - the first thing the camera ray hits within 100 m (else the point 100 m along it), elevation for a 100 m zero.
lift_m = pure('LiftM', KML, 'SelectFloat', X + 2400, SY + 700, ins=[fin('A', None, '%.9g' % B['zero50_elev_rad']), fin('B', None, '%.9g' % B['zero_elev_rad']), ('bPickA', 'bool', '', None, ads_on0, 'false')], out=('real', 'double'))
lift = pure('Lift', KML, 'Multiply_VectorFloat', X + 2650, SY + 600, ins=[vin('A', up), fin('B', lift_m)], out=('struct', '', VEC))
d1 = pure('DirZ', KML, 'Add_VectorVector', X + 2900, SY + 450, ins=[vin('A', d0), vin('B', lift)], out=('struct', '', VEC))
# spread (half angle, degrees) = base x stance multiplier (hip 1.10 / shoulder 1.05 / ADS 0.90) + movement
S, M = B['spread_half_deg'], B['state_mult']
cmc_f = var('GetCMCF', 'CharacterMovement', E + 'CharacterMovementComponent', X + 2400, SY + 1250)
crouch_on = pure('CrouchOnF', E + 'CharacterMovementComponent', 'IsCrouching', X + 2650, SY + 1250, out=('bool',), self_cls=E + 'CharacterMovementComponent', self_link=cmc_f)
ads = var('GetAdsF', 'FurinaADS', E + 'SceneComponent', X + 2400, SY + 800)
sh = var('GetShF', 'FurinaShoulder', E + 'SceneComponent', X + 2400, SY + 900)
ads_on = pure('AdsOnF', E + 'ActorComponent', 'IsActive', X + 2650, SY + 800, out=('bool',), self_cls=E + 'ActorComponent', self_link=ads)
sh_on = pure('ShOnF', E + 'ActorComponent', 'IsActive', X + 2650, SY + 900, out=('bool',), self_cls=E + 'ActorComponent', self_link=sh)
m1 = pure('MulShHip', KML, 'SelectFloat', X + 2900, SY + 900, ins=[fin('A', None, '%g' % M['shoulder']), fin('B', None, '%g' % M['hip']),
          ('bPickA', 'bool', '', None, sh_on, 'false')], out=('real', 'double'))
mult = pure('Mult', KML, 'SelectFloat', X + 3150, SY + 850, ins=[fin('A', None, '%g' % M['ads']), fin('B', m1),
            ('bPickA', 'bool', '', None, ads_on, 'false')], out=('real', 'double'))
cmul = pure('CrouchMul', KML, 'SelectFloat', X + 3150, SY + 1250, ins=[fin('A', None, '%g' % M['crouch']), fin('B', None, '1.0'), ('bPickA', 'bool', '', None, crouch_on, 'false')], out=('real', 'double'))
mult2 = pure('Mult2', KML, 'Multiply_DoubleDouble', X + 3400, SY + 1150, ins=[fin('A', mult), fin('B', cmul)], out=('real', 'double'))
s2 = pure('SprBase', KML, 'Multiply_DoubleDouble', X + 3650, SY + 850, ins=[fin('A', mult), fin('B', None, '%g' % S['base'])], out=('real', 'double'))
vel = pure('MyVel', E + 'Actor', 'GetVelocity', X + 2900, SY + 1050, out=('struct', '', VEC), self_cls=E + 'Actor')
vs = pure('MySpd', KML, 'VSize', X + 3150, SY + 1050, ins=[vin('A', vel)], out=('real', 'double'))
mv = pure('MovePen', KML, 'Multiply_DoubleDouble', X + 3400, SY + 1050, ins=[fin('A', vs), fin('B', None, '%g' % S['per_cm_s'])], out=('real', 'double'))
half = pure('Half', KML, 'Add_DoubleDouble', X + 3650, SY + 900, ins=[fin('A', s2), fin('B', mv)], out=('real', 'double'))
half = pure('CrouchCone', KML, 'Multiply_DoubleDouble', X + 3800, SY + 1050, ins=[fin('A', half), fin('B', cmul)], out=('real', 'double'))
cone = pure('Cone', KML, 'RandomUnitVectorInConeInDegrees', X + 3900, SY + 500, ins=[('ConeDir', 'struct', '', VEC, d1, None),
            ('ConeHalfAngleInDegrees', 'real', 'float', None, half, '0.0')], out=('struct', '', VEC))
rot = pure('ShotRot', KML, 'MakeRotFromX', X + 4150, SY + 500, ins=[vin('X', cone)], out=('struct', '', ROT))
xf = pure('ShotXf', KML, 'MakeTransform', X + 4400, SY + 500, ins=[vin('Location', muz), ('Rotation', 'struct', '', ROT, rot, None),
          ('Scale', 'struct', '', VEC, None, '1.000000,1.000000,1.000000')], out=('struct', '', XF))
C.node('Spawn', '/Script/BlueprintGraph.K2Node_SpawnActorFromClass', [], X + 4650, SY)
C.pin('Spawn', 'execute', 'exec'); C.pin('Spawn', 'then', 'exec', out=True)
C.pin('Spawn', 'Class', 'class', obj=CLS(E + 'Actor'), default_object=BULLET_C)
C.pin('Spawn', 'ReturnValue', 'object', obj="/Script/Engine.BlueprintGeneratedClass'%s'" % BULLET_C, out=True)
C.pin('Spawn', 'SpawnTransform', 'struct', obj=XF); C.link(xf, ('Spawn', 'SpawnTransform'))
C.pin('Spawn', 'CollisionHandlingOverride', 'byte', obj=ENUM(E + 'ESpawnActorCollisionHandlingMethod'), default='AlwaysSpawn')
C.pin('Spawn', 'TransformScaleMethod', 'byte', obj=ENUM(E + 'ESpawnActorScaleMethod'), default='MultiplyWithRoot')
C.pin('Spawn', 'Owner', 'object', obj=CLS(E + 'Actor')); C.link(me, ('Spawn', 'Owner'))
C.pin('Spawn', 'Instigator', 'object', obj=CLS(E + 'Pawn')); C.link(me, ('Spawn', 'Instigator'))
C.link(('Aim', 'then'), ('Spawn', 'execute'))
# recoil: control rotation += (vertical, horizontal) x stance multiplier, per shot
R = B['recoil']; RX = X + 4950
rv = pure('RecV0', KML, 'RandomFloatInRange', RX, SY + 300, ins=[fin('Min', None, '%g' % (R['vertical_deg'] * (1 - R['vertical_jitter']))),
          fin('Max', None, '%g' % (R['vertical_deg'] * (1 + R['vertical_jitter'])))], out=('real', 'double'))
rh = pure('RecH0', KML, 'RandomFloatInRange', RX, SY + 450, ins=[fin('Min', None, '%g' % R['horizontal_min_deg']), fin('Max', None, '%g' % R['horizontal_max_deg'])], out=('real', 'double'))
adsg = pure('AdsGain', KML, 'SelectFloat', RX, SY + 900, ins=[fin('A', None, '%g' % R['ads_gain']), fin('B', None, '1.0'), ('bPickA', 'bool', '', None, ads_on, 'false')], out=('real', 'double'))
fpc = var('GetFPCamR', 'FPCamera', E + 'CameraComponent', RX, SY + 1050)
fp_on = pure('FPOnR', E + 'ActorComponent', 'IsActive', RX + 250, SY + 1050, out=('bool',), self_cls=E + 'ActorComponent', self_link=fpc)
tpg = pure('TpGain', KML, 'SelectFloat', RX + 500, SY + 1000, ins=[fin('A', None, '1.0'), fin('B', None, '%g' % R['tp_gain']), ('bPickA', 'bool', '', None, fp_on, 'false')], out=('real', 'double'))
rg1 = pure('RecG1', KML, 'Multiply_DoubleDouble', RX + 750, SY + 950, ins=[fin('A', mult2), fin('B', adsg)], out=('real', 'double'))
recgain = pure('RecGain', KML, 'Multiply_DoubleDouble', RX + 1000, SY + 950, ins=[fin('A', rg1), fin('B', tpg)], out=('real', 'double'))
rvm = pure('RecV', KML, 'Multiply_DoubleDouble', RX + 250, SY + 300, ins=[fin('A', rv), fin('B', recgain)], out=('real', 'double'))
rhm = pure('RecH', KML, 'Multiply_DoubleDouble', RX + 250, SY + 450, ins=[fin('A', rh), fin('B', recgain)], out=('real', 'double'))
cr2 = pure('CtrlRot2', E + 'Pawn', 'GetControlRotation', RX, SY + 600, out=('struct', '', ROT), self_cls=E + 'Pawn')
call('BreakCtrl2', KML, 'BreakRotator', RX + 250, SY + 600, pure=True)
C.pin('BreakCtrl2', 'InRot', 'struct', obj=ROT); C.link(cr2, ('BreakCtrl2', 'InRot'))
for n in ('Roll', 'Pitch', 'Yaw'): C.pin('BreakCtrl2', n, 'real', 'float', out=True)
np_ = pure('NewPitch', KML, 'Add_DoubleDouble', RX + 500, SY + 350, ins=[fin('A', ('BreakCtrl2', 'Pitch')), fin('B', rvm)], out=('real', 'double'))
ny = pure('NewYaw', KML, 'Add_DoubleDouble', RX + 500, SY + 500, ins=[fin('A', ('BreakCtrl2', 'Yaw')), fin('B', rhm)], out=('real', 'double'))
call('MakeRec', KML, 'MakeRotator', RX + 750, SY + 400, pure=True)
C.pin('MakeRec', 'Roll', 'real', 'float', default='0.0'); C.link(('BreakCtrl2', 'Roll'), ('MakeRec', 'Roll'))
C.pin('MakeRec', 'Pitch', 'real', 'float', default='0.0'); C.link(np_, ('MakeRec', 'Pitch'))
C.pin('MakeRec', 'Yaw', 'real', 'float', default='0.0'); C.link(ny, ('MakeRec', 'Yaw'))
C.pin('MakeRec', 'ReturnValue', 'struct', obj=ROT, out=True)
ctl = pure('MyCtrl', E + 'Pawn', 'GetController', RX + 750, SY + 250, out=('object', '', CLS(E + 'Controller')), self_cls=E + 'Pawn')
call('Recoil', E + 'Controller', 'SetControlRotation', RX + 1000, SY, self_cls=E + 'Controller', self_link=ctl)
C.pin('Recoil', 'NewRotation', 'struct', obj=ROT); C.link(('MakeRec', 'ReturnValue'), ('Recoil', 'NewRotation'))
C.link(('Spawn', 'then'), ('Recoil', 'execute'))

# ---- fire rules (2026-11-15): sprinting (> 220 cm/s, not aiming) -> no shot, the character goes to the shoulder stance (FurinaShoulderAuto
# is released by the Event Tick graph when the fire timer stops); moving -> only shouldered / ADS may fire, hip fire needs < 15 cm/s
def set_active(key, ref, value, x, y):
    call(key, E + 'ActorComponent', 'SetActive', x, y, self_cls=E + 'ActorComponent', self_link=ref)
    C.pin(key, 'bNewActive', 'bool', default=value); C.pin(key, 'bReset', 'bool', default='false')
fvel = pure('FVel', E + 'Actor', 'GetVelocity', X + 3000, SY + 1400, out=('struct', '', VEC), self_cls=E + 'Actor')
fspd = pure('FSpd', KML, 'VSize', X + 3250, SY + 1400, ins=[vin('A', fvel)], out=('real', 'double'))
fast = pure('Fast', KML, 'Greater_DoubleDouble', X + 3500, SY + 1350, ins=[fin('A', fspd), fin('B', None, '220.0')], out=('bool',))
slow = pure('Slow', KML, 'Less_DoubleDouble', X + 3500, SY + 1500, ins=[fin('A', fspd), fin('B', None, '2.0')], out=('bool',))
aiming = pure('AimingF', KML, 'BooleanOR', X + 3500, SY + 1650, ins=[('A', 'bool', '', None, ads_on, 'false'), ('B', 'bool', '', None, sh_on, 'false')], out=('bool',))
notaim = pure('NotAimF', KML, 'Not_PreBool', X + 3750, SY + 1650, ins=[('A', 'bool', '', None, aiming, 'false')], out=('bool',))
sprinting = pure('SprintingF', KML, 'BooleanAND', X + 4000, SY + 1450, ins=[('A', 'bool', '', None, fast, 'false'), ('B', 'bool', '', None, notaim, 'false')], out=('bool',))
canfire = pure('CanFire', KML, 'BooleanOR', X + 4000, SY + 1650, ins=[('A', 'bool', '', None, aiming, 'false'), ('B', 'bool', '', None, slow, 'false')], out=('bool',))
branch('SprintB', sprinting, X + 300, SY - 250); C.link(('Shot', 'then'), ('SprintB', 'execute'))
branch('CanB', canfire, X + 600, SY - 100); C.link(('SprintB', 'else'), ('CanB', 'execute'))
C.link(('CanB', 'then'), ('FaceAim', 'execute'))
shauto = var('GetShAutoF', 'FurinaShoulderAuto', E + 'SceneComponent', X + 300, SY - 600)
set_active('AutoSh', sh, 'true', X + 600, SY - 450); C.link(('SprintB', 'then'), ('AutoSh', 'execute'))
set_active('AutoFlag', shauto, 'true', X + 900, SY - 450); C.link(('AutoSh', 'then'), ('AutoFlag', 'execute'))
cmc_y = var('GetCMCY', 'CharacterMovement', E + 'CharacterMovementComponent', X + 1200, SY - 650)
C.node('AutoYaw', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberName="bUseControllerRotationYaw",bSelfContext=True)'], X + 1200, SY - 450)
C.pin('AutoYaw', 'execute', 'exec'); C.pin('AutoYaw', 'then', 'exec', out=True); C.pin('AutoYaw', 'bUseControllerRotationYaw', 'bool', default='true')
C.link(('AutoFlag', 'then'), ('AutoYaw', 'execute'))
C.node('AutoOrient', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="bOrientRotationToMovement")' % CLS(E + 'CharacterMovementComponent'), 'SelfContextInfo=NotSelfContext'], X + 1500, SY - 450)
C.pin('AutoOrient', 'execute', 'exec'); C.pin('AutoOrient', 'then', 'exec', out=True); C.pin('AutoOrient', 'bOrientRotationToMovement', 'bool', default='false')
C.pin('AutoOrient', 'self', 'object', obj=CLS(E + 'CharacterMovementComponent')); C.link(cmc_y, ('AutoOrient', 'self'))
C.link(('AutoYaw', 'then'), ('AutoOrient', 'execute'))
open(D + r'\fp_fire_char.t3d', 'w', encoding='utf-8', newline='\r\n').write(C.text().replace('K2Node_FP_', 'K2Node_FPF_'))
print('ok', len(A.order), len(C.order))

