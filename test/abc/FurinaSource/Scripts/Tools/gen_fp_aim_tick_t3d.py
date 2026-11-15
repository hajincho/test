"""Character Event Tick nodes for aiming / crouch stances. usage: gen_fp_aim_tick_t3d.py <Data> -> fp_aim_tick.t3d
(2026-11-15 version; the 2026-11-14 Event Tick node in the BP is deleted before this one is pasted)
Tick -> Sequence
  0: movement speed. The tick owns MaxWalkSpeed (and MaxWalkSpeedCrouched, which the engine uses while crouching) while aiming or
     crouching and gives it back once afterwards (FurinaSpeedCap flag).
       walk 120 / sprint 600;  crouched: walk 90 (-25 %) / sprint 360 (-40 %)
       ADS            -> the walk speed of the stance (120 / 90), Shift or not
       shoulder       -> walking: 50 % of the walk speed (60 / 45); sprint key held: 20 % of the sprint speed (120 / 72)
                         (2x the old penalty: the old values were 120 walking and 40 % = 240 running)
  1: shoulder side latch: while NOT shouldered, FurinaShoulderLeft = camera is more than 20 cm on the character's left, so the
     shoulder view goes to the side the third-person camera already is on
  2: third-person shoulder camera (shouldered and not first person):
       CameraBoom.SocketOffset -> (0, side * (30 + 0.08 * arm length), 15), FollowCamera FOV 90 -> 60 (1.5x zoom), eased
  3: FurinaCrouch flag = CharacterMovement.IsCrouching (read by ABP_Furina -> 'Crouch' curve -> CR_FurinaSecondary)
  4: the sprint-fire shoulder (FurinaShoulderAuto) ends when the fire timer 'FurinaRifleShot' is no longer running.
  C (IA_FurinaCrouch, Started): toggles Crouch / UnCrouch."""
import sys
D = sys.argv[1]
src = open(__file__.replace('gen_fp_aim_tick_t3d.py', 'gen_fp_bullet_t3d.py'), encoding='utf-8').read().split('# ======================= bullet actor')[0]
sys.argv = ['x', D]; ns = {'__file__': __file__.replace('gen_fp_aim_tick_t3d.py', 'gen_fp_bullet_t3d.py')}; exec(src, ns)
Graph, kit, CLS, STR, E, VEC, KML, vin, fin = ns['Graph'], ns['kit'], ns['CLS'], ns['STR'], ns['E'], ns['VEC'], ns['KML'], ns['vin'], ns['fin']
KSL = ns['KSL']
WALK, SPRINT, CWALK, CSPRINT = 120.0, 600.0, 90.0, 360.0          # 90 = 120 x 0.75, 360 = 600 x 0.6
SH_WALK_MUL, SH_RUN_MUL = 0.5, 0.2                                # shoulder: half the walk speed, a fifth of the sprint speed
ARM, CAM, CMC, SC = E + 'SpringArmComponent', E + 'CameraComponent', E + 'CharacterMovementComponent', E + 'SceneComponent'

C = Graph(); call, event, pure, var, branch, comp_var = kit(C)
X, Y = -2600, 33000
event('Tick', 'ReceiveTick', 'Actor', X, Y, outs=[('DeltaSeconds', 'real', 'float')])
C.node('Seq', '/Script/BlueprintGraph.K2Node_ExecutionSequence', [], X + 250, Y)
C.pin('Seq', 'execute', 'exec'); [C.pin('Seq', 'then_%d' % i, 'exec', out=True) for i in range(5)]
C.link(('Tick', 'then'), ('Seq', 'execute'))
C.node('Self', '/Script/BlueprintGraph.K2Node_Self', [], X + 100, Y + 1700); me = C.pin('Self', 'self', 'object', 'self', out=True)
def active(key, member, x, y):
    ref = var('Get' + key, member, SC, x, y)
    return pure(key, E + 'ActorComponent', 'IsActive', x + 220, y, out=('bool',), self_cls=E + 'ActorComponent', self_link=ref), ref
def set_active(key, ref, x, y, value=None, link=None):
    call(key, E + 'ActorComponent', 'SetActive', x, y, self_cls=E + 'ActorComponent', self_link=ref)
    C.pin(key, 'bNewActive', 'bool', default=value or 'false')
    if link: C.link(link, (key, 'bNewActive'))
    C.pin(key, 'bReset', 'bool', default='false')
def sel(key, a, b, pick, x, y):
    return pure(key, KML, 'SelectFloat', x, y, ins=[fin('A', a[0], a[1]), fin('B', b[0], b[1]), ('bPickA', 'bool', '', None, pick, 'false')], out=('real', 'double'))
def mul(key, a, b, x, y):
    return pure(key, KML, 'Multiply_DoubleDouble', x, y, ins=[fin('A', a[0], a[1]), fin('B', b[0], b[1])], out=('real', 'double'))
ads_on, _ = active('AdsOnT', 'FurinaADS', X, Y + 300)
sh_on, sh_ref = active('ShOnT', 'FurinaShoulder', X, Y + 420)
cap_on, cap = active('CapOnT', 'FurinaSpeedCap', X, Y + 540)
left_on, left = active('LeftOnT', 'FurinaShoulderLeft', X, Y + 660)
crouch_flag, cflag = active('CrouchFlagT', 'FurinaCrouch', X, Y + 1500)
auto_on, auto = active('AutoOnT', 'FurinaShoulderAuto', X, Y + 1620)
fp_cam = var('GetFPCamT', 'FPCamera', CAM, X, Y + 780)
fp_on = pure('FPOnT', E + 'ActorComponent', 'IsActive', X + 220, Y + 780, out=('bool',), self_cls=E + 'ActorComponent', self_link=fp_cam)
cmc = var('GetCMCT', 'CharacterMovement', CMC, X + 900, Y - 450)
crouch_on = pure('CrouchingT', CMC, 'IsCrouching', X + 1150, Y - 450, out=('bool',), self_cls=CMC, self_link=cmc)
pc = pure('PCT', E + 'GameplayStatics', 'GetPlayerController', X, Y + 900, ins=[('PlayerIndex', 'int', '', None, None, '0')], out=('object', '', CLS(E + 'PlayerController')))
C.pin('PCT', 'WorldContextObject', 'object', obj=CLS('/Script/CoreUObject.Object'), hidden=True)
sprint = pure('Sprint', E + 'PlayerController', 'IsInputKeyDown', X + 250, Y + 900,
              ins=[('Key', 'struct', '', STR('/Script/InputCore.Key'), None, '(KeyName=\\"LeftShift\\")')],
              out=('bool',), self_cls=E + 'PlayerController', self_link=pc)   # IA_FurinaSprint is Left Shift
# ---- 0: speed
aiming = pure('Aiming', KML, 'BooleanOR', X + 500, Y + 350, ins=[('A', 'bool', '', None, ads_on, 'false'), ('B', 'bool', '', None, sh_on, 'false')], out=('bool',))
own = pure('OwnSpeed', KML, 'BooleanOR', X + 750, Y + 350, ins=[('A', 'bool', '', None, aiming, 'false'), ('B', 'bool', '', None, crouch_on, 'false')], out=('bool',))
branch('AimB', own, X + 600, Y - 300); C.link(('Seq', 'then_0'), ('AimB', 'execute'))
walk = sel('WalkSpd', (None, '%g' % CWALK), (None, '%g' % WALK), crouch_on, X + 600, Y + 1000)
run = sel('RunSpd', (None, '%g' % CSPRINT), (None, '%g' % SPRINT), crouch_on, X + 600, Y + 1120)
sh_walk = mul('ShWalk', (walk, '0.0'), (None, '%g' % SH_WALK_MUL), X + 850, Y + 1000)
sh_run = mul('ShRun', (run, '0.0'), (None, '%g' % SH_RUN_MUL), X + 850, Y + 1120)
sh_spd = sel('ShSpd', (sh_run, '0.0'), (sh_walk, '0.0'), sprint, X + 1100, Y + 1050)
aim_spd = sel('AimSpd', (walk, '0.0'), (sh_spd, '0.0'), ads_on, X + 1350, Y + 1000)
free_spd = sel('FreeSpd', (run, '0.0'), (walk, '0.0'), sprint, X + 1350, Y + 1150)
own_spd = sel('OwnSpd', (aim_spd, '0.0'), (free_spd, '0.0'), aiming, X + 1600, Y + 1050)
def set_speed(key, member, value, x, y):
    C.node(key, '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="%s")' % (CLS(CMC), member), 'SelfContextInfo=NotSelfContext'], x, y)
    C.pin(key, 'execute', 'exec'); C.pin(key, 'then', 'exec', out=True)
    C.pin(key, member, 'real', 'float', default='0.0'); C.link(value, (key, member))
    C.pin(key, 'self', 'object', obj=CLS(CMC)); C.link(cmc, (key, 'self'))
    C.pin(key, 'Output_Get', 'real', 'float', out=True)
set_speed('CapSpeed', 'MaxWalkSpeed', own_spd, X + 900, Y - 350); C.link(('AimB', 'then'), ('CapSpeed', 'execute'))
set_speed('CapSpeedC', 'MaxWalkSpeedCrouched', own_spd, X + 1250, Y - 350); C.link(('CapSpeed', 'then'), ('CapSpeedC', 'execute'))
set_active('CapOn', cap, X + 1600, Y - 350, 'true'); C.link(('CapSpeedC', 'then'), ('CapOn', 'execute'))
branch('WasCap', cap_on, X + 900, Y - 150); C.link(('AimB', 'else'), ('WasCap', 'execute'))
set_speed('FreeSpeed', 'MaxWalkSpeed', free_spd, X + 1200, Y - 150); C.link(('WasCap', 'then'), ('FreeSpeed', 'execute'))
set_active('CapOff', cap, X + 1500, Y - 150, 'false'); C.link(('FreeSpeed', 'then'), ('CapOff', 'execute'))
# ---- 1: side latch
branch('ShB', sh_on, X + 600, Y + 100); C.link(('Seq', 'then_1'), ('ShB', 'execute'))
follow = var('GetFollowT', 'FollowCamera', CAM, X + 600, Y + 1300)
camloc = pure('CamLocT', SC, 'K2_GetComponentLocation', X + 850, Y + 1300, out=('struct', '', VEC), self_cls=SC, self_link=follow)
me_loc = pure('MeLocT', E + 'Actor', 'K2_GetActorLocation', X + 850, Y + 1420, out=('struct', '', VEC), self_cls=E + 'Actor')
right = pure('MeRightT', E + 'Actor', 'GetActorRightVector', X + 850, Y + 1540, out=('struct', '', VEC), self_cls=E + 'Actor')
rel = pure('RelT', KML, 'Subtract_VectorVector', X + 1100, Y + 1350, ins=[vin('A', camloc), vin('B', me_loc)], out=('struct', '', VEC))
side_d = pure('SideD', KML, 'Dot_VectorVector', X + 1350, Y + 1400, ins=[vin('A', rel), vin('B', right)], out=('real', 'double'))
is_left = pure('IsLeftT', KML, 'Less_DoubleDouble', X + 1600, Y + 1400, ins=[fin('A', side_d), fin('B', None, '-20.0')], out=('bool',))
set_active('LatchSide', left, X + 900, Y + 150, link=is_left); C.link(('ShB', 'else'), ('LatchSide', 'execute'))
# ---- 2: shoulder camera
not_fp = pure('NotFPT', KML, 'Not_PreBool', X + 500, Y + 780, ins=[('A', 'bool', '', None, fp_on, 'false')], out=('bool',))
tp_sh = pure('TPSh', KML, 'BooleanAND', X + 700, Y + 600, ins=[('A', 'bool', '', None, sh_on, 'false'), ('B', 'bool', '', None, not_fp, 'false')], out=('bool',))
boom = var('GetBoomT', 'CameraBoom', ARM, X + 1100, Y + 500)
C.node('ArmLen', '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberParent="%s",MemberName="TargetArmLength")' % CLS(ARM), 'SelfContextInfo=NotSelfContext'], X + 1350, Y + 600)
C.pin('ArmLen', 'TargetArmLength', 'real', 'float', out=True); C.pin('ArmLen', 'self', 'object', obj=CLS(ARM)); C.link(boom, ('ArmLen', 'self'))
lat0 = mul('Lat0', (('ArmLen', 'TargetArmLength'), '0.0'), (None, '0.08'), X + 1600, Y + 600)
lat1 = pure('Lat1', KML, 'Add_DoubleDouble', X + 1850, Y + 600, ins=[fin('A', lat0), fin('B', None, '30.0')], out=('real', 'double'))
side = sel('SideSign', (None, '-1.0'), (None, '1.0'), left_on, X + 1850, Y + 750)
lat = mul('Lat', (lat1, '0.0'), (side, '0.0'), X + 2100, Y + 650)
ty = sel('TgtY', (lat, '0.0'), (None, '0.0'), tp_sh, X + 2350, Y + 600)
tz = sel('TgtZ', (None, '15.0'), (None, '0.0'), tp_sh, X + 2350, Y + 750)
tgt = pure('TgtOff', KML, 'MakeVector', X + 2600, Y + 650, ins=[fin('X', None, '0.0'), fin('Y', ty), fin('Z', tz)], out=('struct', '', VEC))
cur = comp_var('CurOff', 'SocketOffset', ARM, X + 2350, Y + 450, boom)
newoff = pure('NewOff', KML, 'VInterpTo', X + 2850, Y + 500, ins=[vin('Current', cur), vin('Target', tgt), fin('DeltaTime', ('Tick', 'DeltaSeconds'), '0.0', 'float'),
              fin('InterpSpeed', None, '10.0', 'float')], out=('struct', '', VEC))
C.node('SetOff', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="SocketOffset")' % CLS(ARM), 'SelfContextInfo=NotSelfContext'], X + 3100, Y + 300)
C.pin('SetOff', 'execute', 'exec'); C.pin('SetOff', 'then', 'exec', out=True)
C.pin('SetOff', 'SocketOffset', 'struct', obj=VEC); C.link(newoff, ('SetOff', 'SocketOffset'))
C.pin('SetOff', 'self', 'object', obj=CLS(ARM)); C.link(boom, ('SetOff', 'self'))
C.pin('SetOff', 'Output_Get', 'struct', obj=VEC, out=True)
C.link(('Seq', 'then_2'), ('SetOff', 'execute'))
C.node('CurFov', '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberParent="%s",MemberName="FieldOfView")' % CLS(CAM), 'SelfContextInfo=NotSelfContext'], X + 2600, Y + 900)
C.pin('CurFov', 'FieldOfView', 'real', 'float', out=True); C.pin('CurFov', 'self', 'object', obj=CLS(CAM)); C.link(follow, ('CurFov', 'self'))
tf = sel('TgtFov', (None, '60.0'), (None, '90.0'), tp_sh, X + 2600, Y + 1050)
nf = pure('NewFov', KML, 'FInterpTo', X + 2850, Y + 950, ins=[fin('Current', ('CurFov', 'FieldOfView')), fin('Target', tf), fin('DeltaTime', ('Tick', 'DeltaSeconds'), '0.0', 'float'),
          fin('InterpSpeed', None, '10.0', 'float')], out=('real', 'double'))
call('SetFov', CAM, 'SetFieldOfView', X + 3400, Y + 300, self_cls=CAM, self_link=follow)
C.pin('SetFov', 'InFieldOfView', 'real', 'float', default='90.0'); C.link(nf, ('SetFov', 'InFieldOfView'))
C.link(('SetOff', 'then'), ('SetFov', 'execute'))
# ---- 3: crouch flag
set_active('CrouchFlag', cflag, X + 700, Y + 1900, link=crouch_on); C.link(('Seq', 'then_3'), ('CrouchFlag', 'execute'))
# ---- 4: release the sprint-fire shoulder when the fire timer stopped
timer_on = pure('TimerOnT', KSL, 'K2_IsTimerActive', X + 700, Y + 2200, ins=[('Object', 'object', '', CLS('/Script/CoreUObject.Object'), me, None), ('FunctionName', 'string', '', None, None, 'FurinaRifleShot')], out=('bool',))
no_timer = pure('NoTimerT', KML, 'Not_PreBool', X + 950, Y + 2200, ins=[('A', 'bool', '', None, timer_on, 'false')], out=('bool',))
rel_cond = pure('RelCond', KML, 'BooleanAND', X + 1200, Y + 2100, ins=[('A', 'bool', '', None, auto_on, 'false'), ('B', 'bool', '', None, no_timer, 'false')], out=('bool',))
branch('RelB', rel_cond, X + 1450, Y + 1950); C.link(('Seq', 'then_4'), ('RelB', 'execute'))
set_active('RelAuto', auto, X + 1750, Y + 1950); C.link(('RelB', 'then'), ('RelAuto', 'execute'))
set_active('RelSh', sh_ref, X + 2050, Y + 1950); C.link(('RelAuto', 'then'), ('RelSh', 'execute'))
C.node('RelYaw', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberName="bUseControllerRotationYaw",bSelfContext=True)'], X + 2350, Y + 1950)
C.pin('RelYaw', 'execute', 'exec'); C.pin('RelYaw', 'then', 'exec', out=True); C.pin('RelYaw', 'bUseControllerRotationYaw', 'bool', default='false')
C.link(fp_on, ('RelYaw', 'bUseControllerRotationYaw')); C.link(('RelSh', 'then'), ('RelYaw', 'execute'))
C.node('RelOrient', '/Script/BlueprintGraph.K2Node_VariableSet', ['VariableReference=(MemberParent="%s",MemberName="bOrientRotationToMovement")' % CLS(CMC), 'SelfContextInfo=NotSelfContext'], X + 2650, Y + 1950)
C.pin('RelOrient', 'execute', 'exec'); C.pin('RelOrient', 'then', 'exec', out=True); C.pin('RelOrient', 'bOrientRotationToMovement', 'bool', default='false')
C.pin('RelOrient', 'self', 'object', obj=CLS(CMC)); C.link(cmc, ('RelOrient', 'self'))
C.link(not_fp, ('RelOrient', 'bOrientRotationToMovement')); C.link(('RelYaw', 'then'), ('RelOrient', 'execute'))
# ---- C: crouch toggle (press C to crouch, press again to stand; IA_FurinaCrouch on C, ue_fp_crouch_setup.py)
C.node('CrIA', '/Script/InputBlueprintNodes.K2Node_EnhancedInputAction', ["InputAction=\"/Script/EnhancedInput.InputAction'/Game/Furina/Input/IA_FurinaCrouch.IA_FurinaCrouch'\""], X, Y + 2600)
for pn in ('Triggered', 'Started', 'Ongoing', 'Canceled', 'Completed'): C.pin('CrIA', pn, 'exec', out=True)
C.pin('CrIA', 'ActionValue', 'bool', out=True, default='false')
cr_now = pure('CrNow', CMC, 'IsCrouching', X + 300, Y + 2850, out=('bool',), self_cls=CMC, self_link=cmc)
branch('CrB', cr_now, X + 350, Y + 2600); C.link(('CrIA', 'Started'), ('CrB', 'execute'))
for key, fn, src_pin, yy in (('DoStand', 'UnCrouch', 'then', 2500), ('DoCrouch', 'Crouch', 'else', 2750)):
    call(key, E + 'Character', fn, X + 700, Y + yy, self_cls=E + 'Character', self_link=me)
    C.pin(key, 'bClientSimulation', 'bool', default='false')
    C.link(('CrB', src_pin), (key, 'execute'))
open(D + r'\fp_aim_tick.t3d', 'w', encoding='utf-8', newline='\r\n').write(C.text().replace('K2Node_FP_', 'K2Node_FPT_'))
print('ok', len(C.order))
