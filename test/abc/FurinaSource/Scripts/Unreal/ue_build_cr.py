"""Builds /Game/Furina/CR_FurinaSecondary: speed-proportional cloth flapping + hair motion (Unity FurinaHairRig chains)."""
import unreal, json, traceback, os, math
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
P = json.load(open(os.path.join(S, 'cr_params.json'), encoding='utf-8'))
FR = json.load(open(os.path.join(S, 'fp_rig.json'), encoding='utf-8')) if os.path.exists(os.path.join(S, 'fp_rig.json')) else None
res = {'log': [], 'fail': []}
STAGE_ONLY = os.path.exists(os.path.join(S, 'hair_stage_only'))
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
DEST = '/Game/Furina/CR_FurinaSecondary'
try:
    # Never delete a loaded Control Rig (that corrupts the package): reuse it and rebuild its graph.
    if eal.does_asset_exist(DEST):
        bp = unreal.load_asset(DEST)
    else:
        sk = unreal.load_asset('/Game/Furina/SK_Furina')
        bp = unreal.ControlRigBlueprintFactory.create_control_rig_from_skeletal_mesh_or_skeleton(sk)
        src = bp.get_path_name().split('.')[0]
        log('created', src)
        if src != DEST:
            eal.rename_asset(src, DEST)
            bp = unreal.load_asset(DEST)
    # Curves used by the graph and by animation/debug probes.
    h = bp.get_hierarchy()
    have = [str(k.name) for k in h.get_all_keys(True) if k.type == unreal.RigElementType.CURVE]
    for cv in ('IdleBlink', 'FurinaIdle', 'HairDyn', 'AhogeDyn', 'HairFlow', 'DbgL', 'DbgR', 'DbgW', 'DbgC', 'AimPitch', 'RifleKick', 'RifleReload', 'AimADS', 'AimShoulder', 'ViewTP', 'Crouch', 'ReloadLX', 'ReloadLY', 'ReloadLZ', 'MagState', 'Zip', 'FireHold', 'Prone'):
        if cv not in have:
            log('add curve', cv, bp.get_hierarchy_controller().add_curve(cv, 0.0, False))
    c = bp.get_controller_by_name('RigVMModel') or bp.get_controller()
    graph = c.get_graph()
    bp.set_auto_vm_recompile(False)
    old = [n.get_name() for n in graph.get_nodes() if 'BeginExecution' not in n.get_name()]
    if old: c.remove_nodes_by_name(old, False)
    names = [n.get_name() for n in graph.get_nodes()]
    log('nodes', names)
    found = [n for n in names if 'BeginExecution' in n]
    if found: begin = found[0]
    else:
        node = c.add_unit_node_from_struct_path(unreal.RigUnit_BeginExecution.static_struct().get_path_name(), 'Execute', unreal.Vector2D(400, -300), 'BeginExecution')
        begin = node.get_name() if node else 'BeginExecution'
        log('added begin', begin)

    def struct(n): return getattr(unreal, n).static_struct().get_path_name()
    def add(unit, name, x, y, **defaults):
        node = c.add_unit_node_from_struct_path(struct(unit), 'Execute', unreal.Vector2D(x, y), name)
        if not node: res['fail'].append('add ' + name); return name
        for k, v in defaults.items():
            if not c.set_pin_default_value('%s.%s' % (name, k), v, True, False):
                res['fail'].append('default %s.%s=%s' % (name, k, v))
        return name
    def link(a, b):
        if not c.add_link(a, b, False): res['fail'].append('link %s -> %s' % (a, b))
    exec_pin = None
    def chain_exec(prev, node):
        for pin in ('ExecuteContext', 'ExecutePin'):
            if c.add_link('%s.%s' % (prev, pin), '%s.%s' % (node, pin), False): return node
        res['fail'].append('exec %s -> %s' % (prev, node)); return node
    def V(x, y, z): return '(X=%f,Y=%f,Z=%f)' % (x, y, z)

    # ---------------- speed of the character in the world (cm/s)
    add('RigUnit_GetTransform', 'HipsXf', -1800, 600, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace')
    add('RigUnit_ToWorldSpace_Location', 'HipsWorld', -1550, 600)
    # Animation pelvis sway must never be interpreted as player velocity.
    c.set_pin_default_value('HipsWorld.Value', V(0, 0, 0), True, False)
    add('RigUnit_DeltaFromPreviousVector', 'HipsDelta', -1300, 600)
    link('HipsWorld.World', 'HipsDelta.Value')
    # horizontal travel only: jumping/falling must not count as running speed
    add('RigUnit_MathVectorMul', 'HipsDeltaXY', -1180, 500, B=V(1, 1, 0))
    link('HipsDelta.Delta', 'HipsDeltaXY.A')
    add('RigUnit_MathVectorLength', 'StepLen', -1050, 600)
    link('HipsDeltaXY.Result', 'StepLen.Value')
    add('RigUnit_GetDeltaTime', 'Dt', -1050, 760)
    add('RigUnit_MathFloatMax', 'DtSafe', -850, 760, B='0.004')
    link('Dt.Result', 'DtSafe.A')
    add('RigUnit_MathFloatDiv', 'SpeedRaw', -650, 600)
    link('StepLen.Result', 'SpeedRaw.A'); link('DtSafe.Result', 'SpeedRaw.B')
    add('RigUnit_MathFloatClamp', 'SpeedClamp', -450, 600, Minimum='0', Maximum='1500')   # teleports / respawn
    link('SpeedRaw.Result', 'SpeedClamp.Value')
    add('RigUnit_AccumulateFloatLerp', 'Speed', -250, 600, Blend='6', bIntegrateDeltaTime='True')
    link('SpeedClamp.Result', 'Speed.TargetValue')
    add('RigUnit_MathFloatRemap', 'Run', -50, 600, SourceMinimum=str(P['walk']), SourceMaximum=str(P['sprint']), TargetMinimum='0', TargetMaximum='1', bClamp='True')
    link('Speed.Result', 'Run.Value')
    add('RigUnit_MathFloatRemap', 'Move', -50, 800, SourceMinimum='15', SourceMaximum=str(P['walk']), TargetMinimum='0', TargetMaximum='1', bClamp='True')
    link('Speed.Result', 'Move.Value')
    add('RigUnit_MathFloatAdd', 'Drive', 150, 700)          # 0 idle .. 1 walking .. 2 sprinting
    link('Run.Result', 'Drive.A'); link('Move.Result', 'Drive.B')
    # under-damped follow: trails lift as speed builds and swing forward a little on a sudden stop
    spring = 'RigUnit_SpringInterpV2' if hasattr(unreal, 'RigUnit_SpringInterpV2') else 'RigUnit_SpringInterp'
    log('spring text', getattr(unreal, spring)().export_text())
    add(spring, 'Trail', 350, 700, Strength='6', CriticalDamping='0.4')
    link('Drive.Result', 'Trail.Target')
    # allow only a small forward swing when stopping, so the hem never folds into the legs
    add('RigUnit_MathFloatClamp', 'TrailC', 550, 700, Minimum='-0.12', Maximum='3')
    link('Trail.Result', 'TrailC.Value')
    add('RigUnit_MathFloatAdd', 'Tempo', 350, 900, B='1')
    link('Drive.Result', 'Tempo.A')
    # footstep bounce: hips vertical velocity (rig space) drives a loose spring, so the hem kicks up with every step
    add('RigUnit_DeltaFromPreviousFloat', 'HipsDZ', -1300, 1000)
    link('HipsXf.Transform.Translation.Z', 'HipsDZ.Value')
    add('RigUnit_MathFloatDiv', 'HipsVZ', -1050, 1000)
    link('HipsDZ.Delta', 'HipsVZ.A'); link('DtSafe.Result', 'HipsVZ.B')
    add('RigUnit_MathFloatClamp', 'HipsVZc', -850, 1000, Minimum='-120', Maximum='120')
    link('HipsVZ.Result', 'HipsVZc.Value')
    add('RigUnit_MathFloatMul', 'BobIn', -650, 1000, B='-0.01')      # body drops -> cloth lags upward
    link('HipsVZc.Result', 'BobIn.A')
    add(spring, 'Bob', -450, 1000, Strength='9', CriticalDamping='0.3')
    link('BobIn.Result', 'Bob.Target')

    prev = begin
    def try_exec(prev, node):   # pure nodes have no exec pin: keep the chain where it was
        for pin in ('ExecuteContext', 'ExecutePin'):
            try:
                if c.add_link('%s.%s' % (prev, pin), '%s.%s' % (node, pin), False): return node
            except Exception: pass
        return prev
    Q0 = '(X=0,Y=0,Z=0,W=1)'

    # ---------------- Unity CharacterGroundAndLook slope stance (standing only)
    # traces under each ankle and under the hips; a foot whose ground is lower drops the pelvis (max 22 cm),
    # the other foot is lifted onto its ground with two-bone IK, and the feet tilt 55% toward the ground normal.
    LX, LY = -1800, -2600
    add('RigUnit_MathVectorAdd', 'CStart', LX, LY + 1500, B=V(0, 0, 20))
    link('HipsXf.Transform.Translation', 'CStart.A')    # traces take and return rig space (the unit converts to world itself)
    add('RigUnit_MathVectorAdd', 'CEnd', LX, LY + 1650, B=V(0, 0, -220))
    link('HipsXf.Transform.Translation', 'CEnd.A')
    add('RigUnit_SphereTraceWorld', 'CTrace', LX + 250, LY + 1500, Channel='ECC_Visibility', Radius='3')
    link('CStart.Result', 'CTrace.Start'); link('CEnd.Result', 'CTrace.End')
    prev = try_exec(prev, 'CTrace')
    add('RigUnit_MathFloatSub', 'CHeight', LX + 500, LY + 1500)     # hips height above the ground under them
    link('HipsXf.Transform.Translation.Z', 'CHeight.A'); link('CTrace.HitLocation.Z', 'CHeight.B')
    add('RigUnit_MathFloatRemap', 'CGateLo', LX + 750, LY + 1450, SourceMinimum='60', SourceMaximum='75', TargetMinimum='0', TargetMaximum='1', bClamp='True')
    link('CHeight.Result', 'CGateLo.Value')
    add('RigUnit_MathFloatRemap', 'CGateHi', LX + 750, LY + 1600, SourceMinimum='112', SourceMaximum='130', TargetMinimum='1', TargetMaximum='0', bClamp='True')
    link('CHeight.Result', 'CGateHi.Value')
    add('RigUnit_MathFloatMul', 'CGate', LX + 1000, LY + 1500)
    link('CGateLo.Result', 'CGate.A'); link('CGateHi.Result', 'CGate.B')
    add('RigUnit_MathFloatRemap', 'StandW', LX + 1000, LY + 1700, SourceMinimum='6', SourceMaximum='65', TargetMinimum='1', TargetMaximum='0', bClamp='True')
    link('Speed.Result', 'StandW.Value')
    add('RigUnit_MathFloatMul', 'SlopeWRaw', LX + 1250, LY + 1600)
    link('CGate.Result', 'SlopeWRaw.A'); link('StandW.Result', 'SlopeWRaw.B')
    add('RigUnit_AccumulateFloatLerp', 'SlopeW', LX + 1500, LY + 1600, Blend='8', bIntegrateDeltaTime='True')
    link('SlopeWRaw.Result', 'SlopeW.TargetValue')
    for side, oy in (('Left', 0), ('Right', 700)):
        s = side[0]; y0 = LY + oy
        add('RigUnit_GetTransform', s + 'Ank', LX, y0, Item='(Type=Bone,Name="%s-ankle")' % side, Space='GlobalSpace')
        add('RigUnit_GetTransform', s + 'Thigh', LX, y0 + 150, Item='(Type=Bone,Name="%s-leg")' % side, Space='GlobalSpace')
        add('RigUnit_GetTransform', s + 'Knee', LX, y0 + 300, Item='(Type=Bone,Name="%s-knee")' % side, Space='GlobalSpace')
        add('RigUnit_MathVectorAdd', s + 'TStart', LX + 500, y0, B=V(0, 0, 45))
        link(s + 'Ank.Transform.Translation', s + 'TStart.A')
        add('RigUnit_MathVectorAdd', s + 'TEnd', LX + 500, y0 + 120, B=V(0, 0, -75))
        link(s + 'Ank.Transform.Translation', s + 'TEnd.A')
        add('RigUnit_SphereTraceWorld', s + 'Trace', LX + 750, y0, Channel='ECC_Visibility', Radius='3')
        link(s + 'TStart.Result', s + 'Trace.Start'); link(s + 'TEnd.Result', s + 'Trace.End')
        prev = try_exec(prev, s + 'Trace')
        add('RigUnit_MathFloatSub', s + 'DRaw', LX + 1000, y0)       # ground under this foot relative to the ground under the hips
        link(s + 'Trace.HitLocation.Z', s + 'DRaw.A'); link('CTrace.HitLocation.Z', s + 'DRaw.B')
        add('RigUnit_MathFloatClamp', s + 'DC', LX + 1250, y0, Minimum='-25', Maximum='25')
        link(s + 'DRaw.Result', s + 'DC.Value')
        add('RigUnit_AccumulateFloatLerp', s + 'D', LX + 1500, y0, Blend='12', bIntegrateDeltaTime='True')
        link(s + 'DC.Result', s + 'D.TargetValue')
    add('RigUnit_MathFloatMin', 'DMin', LX + 1750, LY + 350)
    link('LD.Result', 'DMin.A'); link('RD.Result', 'DMin.B')
    add('RigUnit_MathFloatMul', 'DropNeg', LX + 2000, LY + 350, B='-1')
    link('DMin.Result', 'DropNeg.A')
    add('RigUnit_MathFloatClamp', 'Drop', LX + 2250, LY + 350, Minimum='0', Maximum='22')
    link('DropNeg.Result', 'Drop.Value')
    add('RigUnit_MathFloatMul', 'DropW', LX + 2500, LY + 350)
    link('Drop.Result', 'DropW.A'); link('SlopeW.Result', 'DropW.B')
    # Ramp IK with the motion blend. Multiplying by ten made a small run contribution
    # suddenly replace the entire knee pose during walk/run transitions.
    # crouch (no crouch motion exists in the FPS template, so it is procedural): the 'Crouch' curve from ABP_Furina (0/1, set from the
    # character's IsCrouching) is smoothed, then the pelvis goes down by CROUCH_DROP and 8 cm back while both foot targets are lifted by
    # the same amount (ankle target + drop, then the pelvis drop lowers everything): feet stay on the animated ground level, knees bend.
    CROUCH_DROP = P.get('crouch_drop_cm', 38.0)
    add('RigUnit_GetCurveValue', 'CrouchC', LX + 1750, LY + 1900, Curve='Crouch')
    add('RigUnit_AccumulateFloatLerp', 'CrouchW', LX + 2000, LY + 1900, Blend='9', bIntegrateDeltaTime='True')
    link('CrouchC.Value', 'CrouchW.TargetValue')
    add('RigUnit_MathFloatMul', 'CDrop', LX + 2250, LY + 1900, B=str(CROUCH_DROP))
    link('CrouchW.Result', 'CDrop.A')
    add('RigUnit_MathFloatMul', 'CBack', LX + 2250, LY + 2000, B=str(-P.get('crouch_back_cm', 8.0)))
    link('CrouchW.Result', 'CBack.A')
    add('RigUnit_MathFloatMul', 'CBackInverse', LX + 2400, LY + 2000, B='-1')
    link('CBack.Result', 'CBackInverse.A')
    add('RigUnit_MathFloatAdd', 'IKWa', LX + 2250, LY + 550)
    link('SlopeW.Result', 'IKWa.A')
    if not P.get('tfp_locomotion', False): link('Run.Result', 'IKWa.B')
    elif P.get('stride_warp', False): link('Move.Result', 'IKWa.B')   # walking / running: IK on so the foot excursion can be scaled
    # stride warp (2026-11-15): foot targets move toward the pelvis by (1 - s): s = walk_stride at 120 cm/s .. run_stride at 600 cm/s.
    # StrideD = Move * ((walk - 1) + Run * (run - walk)); foot (x, y) offset from the pelvis * StrideD is added to the IK target.
    # The blend-space sample rates are raised by 1/s (ue_tfp_stride.py) so the planted foot still moves with the ground.
    add('RigUnit_MathFloatMul', 'StrideRun', LX + 2250, LY + 700, B=str(P.get('run_stride', 1.0) - P.get('walk_stride', 1.0)))
    link('Run.Result', 'StrideRun.A')
    add('RigUnit_MathFloatAdd', 'StrideSum', LX + 2400, LY + 700, B=str(P.get('walk_stride', 1.0) - 1.0))
    link('StrideRun.Result', 'StrideSum.A')
    add('RigUnit_MathFloatMul', 'StrideD', LX + 2550, LY + 700)
    link('StrideSum.Result', 'StrideD.A'); link('Move.Result', 'StrideD.B')
    add('RigUnit_MathFloatAdd', 'IKWc', LX + 2400, LY + 550)
    link('IKWa.Result', 'IKWc.A')
    if not P.get('tfp_locomotion', False): link('CrouchW.Result', 'IKWc.B')
    add('RigUnit_MathFloatMul', 'IKWs', LX + 2500, LY + 550, B='1')
    link('IKWc.Result', 'IKWs.A')
    add('RigUnit_MathFloatClamp', 'IKW', LX + 2750, LY + 550, Minimum='0', Maximum='1')
    link('IKWs.Result', 'IKW.Value')
    for side, oy in (('Left', 0), ('Right', 700)):
        s = side[0]; y0 = LY + oy; X2 = LX + 1750
        # lift = (d + drop) * w : applied before the pelvis drop, which then lowers both legs by drop * w
        add('RigUnit_MathFloatAdd', s + 'Lift', X2, y0 + 150)
        link(s + 'D.Result', s + 'Lift.A'); link('Drop.Result', s + 'Lift.B')
        add('RigUnit_MathFloatMul', s + 'LiftW', X2 + 250, y0 + 150)
        link(s + 'Lift.Result', s + 'LiftW.A'); link('SlopeW.Result', s + 'LiftW.B')
        add('RigUnit_MathVectorMake', s + 'LiftV', X2 + 500, y0 + 150)
        # sprint only: pull the foot toward the centre line (retargeted run is too wide-legged for Furina).
        # left side is +X, so the left foot moves -X and the right foot +X.
        sign = 1.0 if side == 'Left' else -1.0
        add('RigUnit_MathFloatMul', s + 'Narrow', X2 + 250, y0 + 280, B=str(-sign * P.get('run_narrow_cm', 2.0)))
        link('Run.Result', s + 'Narrow.A')
        add('RigUnit_MathFloatSub', s + 'FX', X2, y0 + 330)           # foot x relative to the pelvis (component space)
        link(s + 'Ank.Transform.Translation.X', s + 'FX.A'); link('HipsXf.Transform.Translation.X', s + 'FX.B')
        add('RigUnit_MathFloatMul', s + 'FXr', X2 + 250, y0 + 330)
        link(s + 'FX.Result', s + 'FXr.A'); link('StrideD.Result', s + 'FXr.B')
        link(s + 'FXr.Result', s + 'LiftV.X')
        # sprint only: shorter fore-aft split (foot Y relative to the hips) and a lower heel kick
        add('RigUnit_MathFloatSub', s + 'FY', X2, y0 + 380)
        link(s + 'Ank.Transform.Translation.Y', s + 'FY.A'); link('HipsXf.Transform.Translation.Y', s + 'FY.B')
        add('RigUnit_MathFloatMul', s + 'FYs', X2 + 120, y0 + 380, B=str(P.get('run_stride', 0.72) - 1.0))
        link(s + 'FY.Result', s + 'FYs.A')
        add('RigUnit_MathFloatMul', s + 'FYr', X2 + 250, y0 + 380)
        link(s + 'FY.Result', s + 'FYr.A'); link('StrideD.Result', s + 'FYr.B')
        add('RigUnit_MathFloatAdd', s + 'LiftYc', X2 + 450, y0 + 380)
        link(s + 'FYr.Result', s + 'LiftYc.A'); link('CBackInverse.Result', s + 'LiftYc.B')
        link(s + 'LiftYc.Result', s + 'LiftV.Y')
        add('RigUnit_MathFloatSub', s + 'FZ', X2, y0 + 480, B='10')
        link(s + 'Ank.Transform.Translation.Z', s + 'FZ.A')
        add('RigUnit_MathFloatMul', s + 'FZs', X2 + 120, y0 + 480, B=str(P.get('run_kick', 0.7) - 1.0))
        link(s + 'FZ.Result', s + 'FZs.A')
        add('RigUnit_MathFloatMul', s + 'FZr', X2 + 250, y0 + 480)
        link(s + 'FZs.Result', s + 'FZr.A'); link('Run.Result', s + 'FZr.B')
        add('RigUnit_MathFloatAdd', s + 'LiftZ', X2 + 380, y0 + 230)
        link(s + 'LiftW.Result', s + 'LiftZ.A'); link(s + 'FZr.Result', s + 'LiftZ.B')
        add('RigUnit_MathFloatAdd', s + 'LiftZc', X2 + 450, y0 + 230)
        link(s + 'LiftZ.Result', s + 'LiftZc.A'); link('CDrop.Result', s + 'LiftZc.B')
        link(s + 'LiftZc.Result', s + 'LiftV.Z')
        add('RigUnit_MathVectorAdd', s + 'Tgt', X2 + 750, y0 + 150)
        link(s + 'Ank.Transform.Translation', s + 'Tgt.A'); link(s + 'LiftV.Result', s + 'Tgt.B')
        # ground normal (world -> rig) and a 55% foot tilt toward it
        add('RigUnit_MathQuaternionFromTwoVectors', s + 'NQ', X2 + 750, y0 + 400, A=V(0, 0, 1))
        link(s + 'Trace.HitNormal', s + 'NQ.B')
        add('RigUnit_MathFloatMul', s + 'TiltT', X2 + 750, y0 + 550, B='0.55')
        link('SlopeW.Result', s + 'TiltT.A')
        add('RigUnit_MathQuaternionSlerp', s + 'TiltQ', X2 + 1000, y0 + 400, A=Q0)
        link(s + 'NQ.Result', s + 'TiltQ.B'); link(s + 'TiltT.Result', s + 'TiltQ.T')
        add('RigUnit_MathQuaternionMul', s + 'FootRot', X2 + 1250, y0 + 400)
        link(s + 'TiltQ.Result', s + 'FootRot.A'); link(s + 'Ank.Transform.Rotation', s + 'FootRot.B')
        # In UE 5.8 this solver passes PoleVector to SolveTwoBoneIK as a POSITION,
        # even when PoleVectorKind is Direction. Anchor it at this thigh, forward
        # (+Y in Furina mesh space) and slightly outward, so blended straight legs
        # cannot flip toward the mesh origin or inherit an inward bend plane.
        add('RigUnit_MathVectorAdd', s + 'PolePos', X2 + 750, y0 + 700,
            B=V(sign * 6.0, 50.0, 0.0))
        link(s + 'Thigh.Transform.Translation', s + 'PolePos.A')
        add('RigUnit_TwoBoneIKSimplePerItem', s + 'IK', X2 + 1500, y0,
            ItemA='(Type=Bone,Name="%s-leg")' % side, ItemB='(Type=Bone,Name="%s-knee")' % side, EffectorItem='(Type=Bone,Name="%s-ankle")' % side,
            PrimaryAxis=V(0, -1, 0), SecondaryAxis=V(0, 0, -1), PoleVectorKind='Location', bPropagateToChildren='True',
            ItemALength='39.40', ItemBLength='41.22')   # thigh / shin lengths (0 would fold the leg up to the hip)
        link(s + 'Tgt.Result', s + 'IK.Effector.Translation'); link(s + 'FootRot.Result', s + 'IK.Effector.Rotation')
        link(s + 'PolePos.Result', s + 'IK.PoleVector'); link('IKW.Result', s + 'IK.Weight')
        prev = chain_exec(prev, s + 'IK')
    add('RigUnit_MathVectorMake', 'DropV', LX + 2750, LY + 350, X='0')
    add('RigUnit_MathFloatAdd', 'DropTot', LX + 2500, LY + 450)
    link('DropW.Result', 'DropTot.A'); link('CDrop.Result', 'DropTot.B')
    add('RigUnit_MathFloatMul', 'DropVZ', LX + 2600, LY + 450, B='-1')
    link('DropTot.Result', 'DropVZ.A'); link('DropVZ.Result', 'DropV.Z'); link('CBack.Result', 'DropV.Y')
    add('RigUnit_MathVectorAdd', 'HipsLow', LX + 3000, LY + 350)
    link('HipsXf.Transform.Translation', 'HipsLow.A'); link('DropV.Result', 'HipsLow.B')
    add('RigUnit_SetTranslation', 'HipsDrop', LX + 3250, LY + 350, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace', bPropagateToChildren='True')
    link('HipsLow.Result', 'HipsDrop.Value')
    prev = chain_exec(prev, 'HipsDrop')

    # ---------------- rifle stance (free FPS template motions, always held in 1st and 3rd person).
    # Gun frame G sits in front of the neck in component axes, pitched by the aim (AimPitch curve from ABP_Furina,
    # degrees) plus recoil (RifleKick curve from the fire montage). Both wrists are placed on the rifle with
    # two-bone IK; the left hand moves to the magazine well while the reload montage's RifleReload curve is up.
    if FR:
        RX2, RY2 = -1800, -7600
        def Q(q): return '(X=%f,Y=%f,Z=%f,W=%f)' % tuple(q)
        add('RigUnit_GetCurveValue', 'AimPitchC', RX2, RY2, Curve='AimPitch')
        add('RigUnit_MathFloatClamp', 'AimPitchDeg', RX2 + 250, RY2, Minimum='-60', Maximum='60')
        link('AimPitchC.Value', 'AimPitchDeg.Value')
        add('RigUnit_GetCurveValue', 'KickC', RX2, RY2 + 150, Curve='RifleKick')
        add('RigUnit_MathFloatMul', 'KickDeg', RX2 + 250, RY2 + 150, B='4')
        link('KickC.Value', 'KickDeg.A')
        add('RigUnit_MathFloatAdd', 'PitchDeg', RX2 + 500, RY2)
        link('AimPitchDeg.Result', 'PitchDeg.A'); link('KickDeg.Result', 'PitchDeg.B')
        add('RigUnit_MathFloatMul', 'PitchRad', RX2 + 750, RY2, B=str(math.pi / 180))
        link('PitchDeg.Result', 'PitchRad.A')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'AimQ', RX2 + 1000, RY2, Axis=V(1, 0, 0))   # +pitch: forward tilts up
        link('PitchRad.Result', 'AimQ.Angle')
        # aim states from ABP_Furina (0/1 curves, smoothed here): AimShoulder = right mouse held, AimADS = right mouse tapped
        PO = FR['poses']
        ADS_BLEND = PO.get('ads_blend', 5.25)       # ADS pose blend rate per second: 14 -> 21 (1.5x) -> 42 (2x of that) -> 10.5 (1/4 of that) -> 5.25 (1/2 of that = 0.375x the original, 2026-11-15); the shoulder blend stays 14
        for cv, node in (('AimShoulder', 'ShW'), ('AimADS', 'AdsW')):
            add('RigUnit_GetCurveValue', node + 'C', RX2 - 250, RY2 + 900 + len(node) * 40, Curve=cv)
            add('RigUnit_AccumulateFloatLerp', node, RX2, RY2 + 900 + len(node) * 40, Blend=str(ADS_BLEND if node == 'AdsW' else 14.0), bIntegrateDeltaTime='True')
            link(node + 'C.Value', node + '.TargetValue')
        # offsets relative to the eye (gen_fp_poses.py / set_fp_poses.py: clip-free with a 4 cm near plane, arms reach)
        add('RigUnit_MathVectorLerp', 'OffHS', RX2 + 250, RY2 + 300, A=V(*PO['hip']), B=V(*PO['shoulder']))
        link('ShW.Result', 'OffHS.T')
        add('RigUnit_MathVectorLerp', 'OffAim', RX2 + 450, RY2 + 300)
        link('OffHS.Result', 'OffAim.A'); link('AdsW.Result', 'OffAim.T')
        c.set_pin_default_value('OffAim.B', V(*PO['ads']), True, False)
        add('RigUnit_MathFloatMul', 'KickBack', RX2 + 500, RY2 + 450, B='-3')
        # ADS: the kick-back toward the eye is cut to 30 % so the rear sight can not be pushed through the near plane while firing
        add('RigUnit_MathFloatRemap', 'KickGain', RX2 + 350, RY2 + 500, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0.3', bClamp='True')
        link('AdsW.Result', 'KickGain.Value')
        add('RigUnit_MathFloatMul', 'KickC2', RX2 + 450, RY2 + 470)
        link('KickC.Value', 'KickC2.A'); link('KickGain.Result', 'KickC2.B')
        link('KickC2.Result', 'KickBack.A')
        add('RigUnit_MathVectorMake', 'KickV', RX2 + 650, RY2 + 450, X='0', Z='0')
        link('KickBack.Result', 'KickV.Y')
        add('RigUnit_MathVectorAdd', 'GOffV', RX2 + 750, RY2 + 300)
        link('OffAim.Result', 'GOffV.A'); link('KickV.Result', 'GOffV.B')
        # sprint carry only while not aiming: weight = Run * (1 - max(shoulder, ads))
        add('RigUnit_MathFloatMax', 'AimAny', RX2 + 250, RY2 + 1100)
        link('ShW.Result', 'AimAny.A'); link('AdsW.Result', 'AimAny.B')
        add('RigUnit_MathFloatRemap', 'NotAim', RX2 + 450, RY2 + 1100, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        link('AimAny.Result', 'NotAim.Value')
        add('RigUnit_MathFloatMul', 'RunW', RX2 + 650, RY2 + 1100)
        link('Run.Result', 'RunW.A'); link('NotAim.Result', 'RunW.B')
        add('RigUnit_MathVectorScale', 'SprintOff', RX2 + 750, RY2 + 450, Value=V(*PO['sprint_off']))
        link('RunW.Result', 'SprintOff.Factor')
        add('RigUnit_MathVectorAdd', 'GOffS', RX2 + 900, RY2 + 350)
        link('GOffV.Result', 'GOffS.A'); link('SprintOff.Result', 'GOffS.B')
        # third person only (ViewTP curve from ABP_Furina = FPCamera inactive): carry the rifle off the face, not for ADS
        add('RigUnit_GetCurveValue', 'ViewTPC', RX2 - 250, RY2 + 1300, Curve='ViewTP')
        add('RigUnit_AccumulateFloatLerp', 'TpW0', RX2, RY2 + 1300, Blend='10', bIntegrateDeltaTime='True')
        link('ViewTPC.Value', 'TpW0.TargetValue')
        add('RigUnit_MathFloatRemap', 'NotAds', RX2 + 250, RY2 + 1300, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        link('AdsW.Result', 'NotAds.Value')
        add('RigUnit_MathFloatMul', 'TpW', RX2 + 450, RY2 + 1300)
        link('TpW0.Result', 'TpW.A'); link('NotAds.Result', 'TpW.B')
        add('RigUnit_MathVectorLerp', 'TpD', RX2 + 450, RY2 + 1450, A=V(*PO['tp_hip_d']), B=V(*PO['tp_sh_d']))
        link('ShW.Result', 'TpD.T')
        add('RigUnit_MathVectorScale', 'TpOff', RX2 + 650, RY2 + 1450)
        link('TpD.Result', 'TpOff.Value'); link('TpW.Result', 'TpOff.Factor')
        # sprint sway with the arms (run loop phase, BOB in set_fp_poses.py), weighted by the sprint carry weight RunW
        BOB = PO['bob']
        add('RigUnit_TimeLoop', 'BobT', RX2, RY2 + 1650, Duration=str(BOB['period']), Normalize='True')
        add('RigUnit_MathFloatMul', 'BobPh', RX2 + 250, RY2 + 1650, B=str(2 * math.pi))
        link('BobT.Relative', 'BobPh.A')
        add('RigUnit_MathFloatSin', 'BobSin', RX2 + 450, RY2 + 1650)
        link('BobPh.Result', 'BobSin.Value')
        add('RigUnit_MathFloatMul', 'BobPh2', RX2 + 450, RY2 + 1750, B='2')
        link('BobPh.Result', 'BobPh2.A')
        add('RigUnit_MathFloatCos', 'BobCos2', RX2 + 650, RY2 + 1750)
        link('BobPh2.Result', 'BobCos2.Value')
        add('RigUnit_MathFloatMul', 'BobSinW', RX2 + 650, RY2 + 1650)
        link('BobSin.Result', 'BobSinW.A'); link('RunW.Result', 'BobSinW.B')
        add('RigUnit_MathFloatMul', 'BobCosW', RX2 + 850, RY2 + 1750)
        link('BobCos2.Result', 'BobCosW.A'); link('RunW.Result', 'BobCosW.B')
        add('RigUnit_MathFloatMul', 'BobX', RX2 + 850, RY2 + 1600, B=str(-BOB['side_cm']))
        link('BobSinW.Result', 'BobX.A')
        add('RigUnit_MathFloatMul', 'BobZ', RX2 + 1050, RY2 + 1750, B=str(-BOB['bob_cm']))
        link('BobCosW.Result', 'BobZ.A')
        add('RigUnit_MathVectorMake', 'BobV', RX2 + 1050, RY2 + 1600, Y='0')
        link('BobX.Result', 'BobV.X'); link('BobZ.Result', 'BobV.Z')
        add('RigUnit_MathVectorAdd', 'GOffTP', RX2 + 900, RY2 + 250)
        link('GOffS.Result', 'GOffTP.A'); link('TpOff.Result', 'GOffTP.B')
        add('RigUnit_MathVectorAdd', 'GOffB', RX2 + 950, RY2 + 250)
        link('GOffTP.Result', 'GOffB.A'); link('BobV.Result', 'GOffB.B')
        add('RigUnit_MathFloatMul', 'BobRoll', RX2 + 850, RY2 + 1900, B=str(math.radians(BOB['roll_deg'])))
        link('BobSinW.Result', 'BobRoll.A')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'BobRollQ', RX2 + 1050, RY2 + 1900, Axis=V(0, 1, 0))
        link('BobRoll.Result', 'BobRollQ.Angle')
        add('RigUnit_MathFloatMul', 'BobYaw', RX2 + 850, RY2 + 2000, B=str(math.radians(BOB['yaw_deg'])))
        link('BobSinW.Result', 'BobYaw.A')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'BobYawQ', RX2 + 1050, RY2 + 2000, Axis=V(0, 0, 1))
        link('BobYaw.Result', 'BobYawQ.Angle')
        add('RigUnit_MathQuaternionMul', 'BobQ', RX2 + 1250, RY2 + 1950)
        link('BobYawQ.Result', 'BobQ.A'); link('BobRollQ.Result', 'BobQ.B')
        add('RigUnit_MathQuaternionRotateVector', 'GOffR', RX2 + 1000, RY2 + 300)
        link('AimQ.Result', 'GOffR.Transform'); link('GOffB.Result', 'GOffR.Vector')
        # anchor = the first-person eye (FPCamera socket point on Head): the rifle rides with the head, so head-bobbing
        # motions (jump lean: eye moved 11 cm forward / 19 cm down) can no longer push the camera into the rifle
        add('RigUnit_GetTransform', 'EyeXf', RX2 + 1000, RY2 + 500, Item='(Type=Bone,Name="Head")', Space='GlobalSpace')
        add('RigUnit_MathTransformTransformVector', 'EyePos', RX2 + 1100, RY2 + 500, Location=V(*FR['cam_head_local']))
        link('EyeXf.Transform', 'EyePos.Transform')
        add('RigUnit_MathVectorAdd', 'GPos', RX2 + 1250, RY2 + 300)
        link('EyePos.Result', 'GPos.A'); link('GOffR.Result', 'GPos.B')
        add('RigUnit_MathQuaternionSlerp', 'SprintQ', RX2 + 1000, RY2 - 200, A='(X=0,Y=0,Z=0,W=1)', B=Q(PO['sprint_q']))
        link('RunW.Result', 'SprintQ.T')
        add('RigUnit_MathQuaternionMul', 'GunSprint', RX2 + 1100, RY2 - 100, B=Q(FR['gun_q']))
        link('SprintQ.Result', 'GunSprint.A')
        # ADS: rifle upright with the sight line on the eye axis
        add('RigUnit_MathQuaternionSlerp', 'GunAds', RX2 + 1150, RY2 - 50, B=Q(PO['ads_q']))
        link('GunSprint.Result', 'GunAds.A'); link('AdsW.Result', 'GunAds.T')
        add('RigUnit_MathQuaternionMul', 'GunBob', RX2 + 1200, RY2 - 50)
        link('BobQ.Result', 'GunBob.A'); link('GunAds.Result', 'GunBob.B')
        add('RigUnit_MathQuaternionMul', 'GRot', RX2 + 1250, RY2)
        link('AimQ.Result', 'GRot.A'); link('GunBob.Result', 'GRot.B')
        add('RigUnit_GetCurveValue', 'ReloadC', RX2, RY2 + 700, Curve='RifleReload')
        add('RigUnit_MathFloatClamp', 'ReloadW', RX2 + 250, RY2 + 700, Minimum='0', Maximum='1')
        link('ReloadC.Value', 'ReloadW.Value')
        # M4 handguard grip: wrist 2 cm further forward, 1.2 cm up and 0.8 cm closer to the barrel than the Honey Badger template hold (left_grip_tweak in fp_rig.json;
        # the left arm is only 39 cm - when the goal is out of reach the IK stops at full extension, ~1 cm short)
        TL = [a + b for a, b in zip(FR['t_l'], FR.get('left_grip_tweak', (0, 0, 0)))]
        add('RigUnit_MathVectorLerp', 'LHandOff', RX2 + 500, RY2 + 700, A=V(*TL), B=V(*TL))   # the reload path now comes from the ReloadL* curves
        link('ReloadW.Result', 'LHandOff.T')
        add('RigUnit_MathFloatMul', 'LBack', RX2 + 750, RY2 + 700, B=str(-PO['tp_lback']))
        link('TpW.Result', 'LBack.A')
        add('RigUnit_MathVectorMake', 'LBackV', RX2 + 950, RY2 + 700, X='0', Z='0')
        add('RigUnit_MathFloatMul', 'ADSLeftBack', RX2 + 750, RY2 + 800, B=str(-PO.get('ads_lback',0)))
        link('AdsW.Result', 'ADSLeftBack.A')
        add('RigUnit_MathFloatAdd', 'AllLeftBack', RX2 + 900, RY2 + 800)
        link('LBack.Result', 'AllLeftBack.A');link('ADSLeftBack.Result','AllLeftBack.B')
        link('AllLeftBack.Result', 'LBackV.Y')
        add('RigUnit_MathVectorAdd', 'LHandOff2', RX2 + 1150, RY2 + 700)
        link('LHandOff.Result', 'LHandOff2.A'); link('LBackV.Result', 'LHandOff2.B')
        # head follows half of the aim pitch (runs BEFORE the arms so the eye point below sees the final head) (third-person look; the FP camera uses the control rotation itself)
        # ---- prone (2026-11-15; curve 'Prone' from ABP_Furina = FurinaProne flag): the whole skeleton (Hips is the single root) is rotated about the feet (mesh origin, X = lateral axis) by
        # poses.prone.angle_deg (-90: head forward, face down) and shifted (back so the body is centred on the capsule, up by half the body thickness). Rigid: Hips rotation, then Hips
        # translation, both propagated to all children. Everything after this (head, spine, arms, rifle) works in the same upright component space.
        PR = PO.get('prone', {'angle_deg': -90.0, 'shift': [0.0, -70.0, 14.0], 'head_deg': 80.0, 'spine_deg': 8.0, 'chest_deg': 10.0})
        add('RigUnit_GetCurveValue', 'ProneC', RX2 - 250, RY2 + 3300, Curve='Prone')
        add('RigUnit_AccumulateFloatLerp', 'ProneW', RX2, RY2 + 3300, Blend='4', bIntegrateDeltaTime='True'); link('ProneC.Value', 'ProneW.TargetValue')
        add('RigUnit_MathFloatRemap', 'NotProne', RX2 + 250, RY2 + 3300, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True'); link('ProneW.Result', 'NotProne.Value')
        add('RigUnit_MathFloatMul', 'ProneAng', RX2 + 250, RY2 + 3400, B=str(math.radians(PR['angle_deg']))); link('ProneW.Result', 'ProneAng.A')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'ProneQ', RX2 + 500, RY2 + 3400, Axis=V(1, 0, 0)); link('ProneAng.Result', 'ProneQ.Angle')
        add('RigUnit_GetTransform', 'PHipXf', RX2 + 500, RY2 + 3500, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace')
        add('RigUnit_MathQuaternionMul', 'PHipRot', RX2 + 750, RY2 + 3400); link('ProneQ.Result', 'PHipRot.A'); link('PHipXf.Transform.Rotation', 'PHipRot.B')
        add('RigUnit_MathQuaternionRotateVector', 'PHipRel', RX2 + 750, RY2 + 3500); link('ProneQ.Result', 'PHipRel.Transform'); link('PHipXf.Transform.Translation', 'PHipRel.Vector')
        add('RigUnit_MathVectorScale', 'PShift', RX2 + 750, RY2 + 3600, Value=V(*PR['shift'])); link('ProneW.Result', 'PShift.Factor')
        add('RigUnit_MathVectorAdd', 'PHipPos', RX2 + 1000, RY2 + 3500); link('PHipRel.Result', 'PHipPos.A'); link('PShift.Result', 'PHipPos.B')
        add('RigUnit_SetRotation', 'PHipSetR', RX2 + 1250, RY2 + 3400, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace', bPropagateToChildren='True'); link('PHipRot.Result', 'PHipSetR.Value')
        add('RigUnit_SetTranslation', 'PHipSetT', RX2 + 1500, RY2 + 3400, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace', bPropagateToChildren='True'); link('PHipPos.Result', 'PHipSetT.Value')
        prev = chain_exec(prev, 'PHipSetR'); prev = chain_exec(prev, 'PHipSetT')
        # cape / skirt drape while prone (poses.prone.cape = {HB root bone: degrees about the mesh X axis}, measured with ue_cape_probe.py in the prone idle pose): the chains hang from the waist
        # and, with the body lying face down, stand up into the air (flare of 25-45 deg above the legs). Every root bone is rotated about X by phi * ProneW (propagated to its whole chain) so the
        # chain direction ends up almost horizontal toward the feet (cape_target_z = -0.15) and the coat rests on the legs instead of floating.
        for root, phi in PR.get('cape', {}).items():
            cn = 'Cape' + root
            add('RigUnit_MathFloatMul', cn + 'A', RX2 + 1750, RY2 + 3700, B=str(math.radians(phi))); link('ProneW.Result', cn + 'A.A')
            add('RigUnit_MathQuaternionFromAxisAndAngle', cn + 'Q', RX2 + 2000, RY2 + 3700, Axis=V(1, 0, 0)); link(cn + 'A.Result', cn + 'Q.Angle')
            add('RigUnit_GetTransform', cn + 'Xf', RX2 + 2000, RY2 + 3800, Item='(Type=Bone,Name="%s")' % root, Space='GlobalSpace')
            add('RigUnit_MathQuaternionMul', cn + 'Rot', RX2 + 2250, RY2 + 3700); link(cn + 'Q.Result', cn + 'Rot.A'); link(cn + 'Xf.Transform.Rotation', cn + 'Rot.B')
            add('RigUnit_SetRotation', cn + 'Set', RX2 + 2500, RY2 + 3700, Item='(Type=Bone,Name="%s")' % root, Space='GlobalSpace', bPropagateToChildren='True'); link(cn + 'Rot.Result', cn + 'Set.Value')
            prev = chain_exec(prev, cn + 'Set')
        add('RigUnit_MathFloatMul', 'HeadPitch', RX2 + 1000, RY2 + 1800, B=str(0.5 * math.pi / 180))
        link('AimPitchDeg.Result', 'HeadPitch.A')
        # prone: the head is lifted (+head_deg about X) so the face looks forward instead of down at the ground
        add('RigUnit_MathFloatMul', 'HeadProne', RX2 + 1000, RY2 + 1700, B=str(math.radians(PR['head_deg']))); link('ProneW.Result', 'HeadProne.A')
        add('RigUnit_MathFloatAdd', 'HeadPitchP', RX2 + 1125, RY2 + 1750); link('HeadPitch.Result', 'HeadPitchP.A'); link('HeadProne.Result', 'HeadPitchP.B')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'HeadQ', RX2 + 1250, RY2 + 1800, Axis=V(1, 0, 0))
        link('HeadPitchP.Result', 'HeadQ.Angle')
        add('RigUnit_GetTransform', 'HeadXf', RX2 + 1250, RY2 + 1950, Item='(Type=Bone,Name="Head")', Space='GlobalSpace')
        add('RigUnit_MathQuaternionMul', 'HeadRot', RX2 + 1500, RY2 + 1800)
        link('HeadQ.Result', 'HeadRot.A'); link('HeadXf.Transform.Rotation', 'HeadRot.B')
        add('RigUnit_SetRotation', 'HeadAim', RX2 + 1750, RY2 + 1800, Item='(Type=Bone,Name="Head")', Space='GlobalSpace', bPropagateToChildren='True')
        link('HeadRot.Result', 'HeadAim.Value')
        prev = chain_exec(prev, 'HeadAim')
        # real reload: left hand path from the template (curves ReloadLX/Y/Z = gun-frame delta, cm, written by ue_reload_motion.py)
        for ax in 'XYZ':
            add('RigUnit_GetCurveValue', 'RLC' + ax, RX2 + 1300, RY2 + 760 + 60 * 'XYZ'.index(ax), Curve='ReloadL' + ax)
        add('RigUnit_MathVectorMake', 'RLV', RX2 + 1500, RY2 + 800)
        link('RLCX.Value', 'RLV.X'); link('RLCY.Value', 'RLV.Y'); link('RLCZ.Value', 'RLV.Z')
        add('RigUnit_MathVectorAdd', 'LHandOff3', RX2 + 1650, RY2 + 750)
        link('LHandOff2.Result', 'LHandOff3.A'); link('RLV.Result', 'LHandOff3.B')
        # idle rest pose (2026-11-15, third person only): standing still, not aiming, not reloading -> the rifle is carried diagonally across the chest (muzzle up and to the
        # right, butt low on the left) with both hands on it (low-ready / port arms like a soldier at ease) instead of pointing forward. Weight RestW = TpW * NotAim * (1 - Move) * (1 - Reload),
        # smoothed; the gun frame (position / rotation) is blended toward the rest frame before the hands are placed. All values are in mesh space (X left, Y forward, Z up), cm / degrees.
        # (rev. 2026-11-15 b: muzzle DOWN and to the left across the body like a soldier at ease - yaw -60 deg (toward the left), pitch -50 deg; right hand on the grip in front of the
        # belly, left hand on the handguard start, butt in front of the right chest; geometry chosen with Data/m4_geometry.json so both hands are within the 39 cm arm reach)
        RP = PO.get('rest', {'yaw_deg': -60.0, 'pitch_deg': -50.0, 'off': [21.07, 22.51, -24.86]})
        add('RigUnit_MathFloatRemap', 'NotMove', RX2 + 250, RY2 + 2300, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        link('Move.Result', 'NotMove.Value')
        add('RigUnit_MathFloatRemap', 'NotReload', RX2 + 250, RY2 + 2400, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        link('ReloadW.Result', 'NotReload.Value')
        add('RigUnit_MathFloatMul', 'RestA', RX2 + 500, RY2 + 2300); link('TpW.Result', 'RestA.A'); link('NotAim.Result', 'RestA.B')
        add('RigUnit_MathFloatMul', 'RestB', RX2 + 700, RY2 + 2300); link('RestA.Result', 'RestB.A'); link('NotMove.Result', 'RestB.B')
        add('RigUnit_MathFloatMul', 'RestC', RX2 + 900, RY2 + 2300); link('RestB.Result', 'RestC.A'); link('NotReload.Result', 'RestC.B')
        # fire input (curve FireHold from ABP_Furina, flag FurinaFireHold set by ue_fire_hold.py: up to 2.5 s after the last FurinaRifleShot event) cancels the rest pose -> normal third-person rifle pose
        add('RigUnit_GetCurveValue', 'FireC', RX2 + 250, RY2 + 2500, Curve='FireHold')
        add('RigUnit_AccumulateFloatLerp', 'FireW', RX2 + 500, RY2 + 2500, Blend='14', bIntegrateDeltaTime='True'); link('FireC.Value', 'FireW.TargetValue')
        add('RigUnit_MathFloatRemap', 'NotFire', RX2 + 750, RY2 + 2500, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True'); link('FireW.Result', 'NotFire.Value')
        add('RigUnit_MathFloatMul', 'RestD0', RX2 + 1000, RY2 + 2500); link('RestC.Result', 'RestD0.A'); link('NotFire.Result', 'RestD0.B')
        add('RigUnit_MathFloatMul', 'RestD', RX2 + 1050, RY2 + 2550); link('RestD0.Result', 'RestD.A'); link('NotProne.Result', 'RestD.B')   # no rest pose while prone
        add('RigUnit_AccumulateFloatLerp', 'RestW', RX2 + 1100, RY2 + 2300, Blend='5', bIntegrateDeltaTime='True'); link('RestD.Result', 'RestW.TargetValue')
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'RestQz', RX2 + 1000, RY2 + 2450, Axis=V(0, 0, 1), Angle=str(math.radians(RP['yaw_deg'])))
        add('RigUnit_MathQuaternionFromAxisAndAngle', 'RestQx', RX2 + 1000, RY2 + 2550, Axis=V(1, 0, 0), Angle=str(math.radians(RP['pitch_deg'])))
        add('RigUnit_MathQuaternionMul', 'RestQ0', RX2 + 1250, RY2 + 2450); link('RestQz.Result', 'RestQ0.A'); link('RestQx.Result', 'RestQ0.B')
        add('RigUnit_MathQuaternionMul', 'RestQ', RX2 + 1450, RY2 + 2450); link('RestQ0.Result', 'RestQ.A'); link('GunBob.Result', 'RestQ.B')
        # RestWF = RestW * NotAim: the slow smoothing (5/s) only applies when entering the rest pose; leaving it for shoulder / ADS follows the fast aim weights (14/s), so a third-person
        # ADS tap no longer waits ~1 s for the rifle to travel from the chest to the sight (probe: ue_ads_time_probe.py)
        add('RigUnit_MathFloatMul', 'RestWF0', RX2 + 1350, RY2 + 2300); link('RestW.Result', 'RestWF0.A'); link('NotAim.Result', 'RestWF0.B')
        add('RigUnit_MathFloatMul', 'RestWF1', RX2 + 1450, RY2 + 2300); link('RestWF0.Result', 'RestWF1.A'); link('NotFire.Result', 'RestWF1.B')
        add('RigUnit_MathFloatMul', 'RestWF', RX2 + 1550, RY2 + 2300); link('RestWF1.Result', 'RestWF.A'); link('NotProne.Result', 'RestWF.B')
        add('RigUnit_MathQuaternionSlerp', 'GRotR', RX2 + 1650, RY2 + 2450); link('GRot.Result', 'GRotR.A'); link('RestQ.Result', 'GRotR.B'); link('RestWF.Result', 'GRotR.T')
        # anchored to the right shoulder joint (does not move with the head pitch / look direction, unlike the eye point): rest position = Right-arm + off (mesh space, cm)
        add('RigUnit_GetTransform', 'RArmXf', RX2 + 1000, RY2 + 2750, Item='(Type=Bone,Name="Right-arm")', Space='GlobalSpace')
        add('RigUnit_MathVectorAdd', 'RestPos', RX2 + 1250, RY2 + 2650, B=V(*RP['off'])); link('RArmXf.Transform.Translation', 'RestPos.A')
        add('RigUnit_MathVectorLerp', 'GPosR', RX2 + 1650, RY2 + 2650); link('GPos.Result', 'GPosR.A'); link('RestPos.Result', 'GPosR.B'); link('RestWF.Result', 'GPosR.T')
        # straighten the back in the rest pose: the idle animation leans forward (PIE probe: Spine>Chest 20 deg, Hips>Head 13.8 deg), so Spine and Chest are tilted back by poses.rest.back_deg
        # (about the mesh X axis, weighted by RestWF, propagated to the children incl. shoulders / head) before the arms are placed
        for bone, deg in (('Spine', RP.get('back_deg', {}).get('Spine', 6.0)), ('Chest', RP.get('back_deg', {}).get('Chest', 6.0))):
            bn = 'Back' + bone
            add('RigUnit_MathFloatMul', bn + 'A', RX2 + 1750, RY2 + 2900 + (0 if bone == 'Spine' else 300), B=str(math.radians(deg))); link('RestWF.Result', bn + 'A.A')
            # prone: the chest is arched up (poses.prone.spine_deg / chest_deg) on top of the rest-pose back straightening
            add('RigUnit_MathFloatMul', bn + 'P', RX2 + 1875, RY2 + 2900 + (0 if bone == 'Spine' else 300), B=str(math.radians(PR['spine_deg'] if bone == 'Spine' else PR['chest_deg']))); link('ProneW.Result', bn + 'P.A')
            add('RigUnit_MathFloatAdd', bn + 'S', RX2 + 1940, RY2 + 2900 + (0 if bone == 'Spine' else 300)); link(bn + 'A.Result', bn + 'S.A'); link(bn + 'P.Result', bn + 'S.B')
            add('RigUnit_MathQuaternionFromAxisAndAngle', bn + 'Q', RX2 + 2000, RY2 + 2900 + (0 if bone == 'Spine' else 300), Axis=V(1, 0, 0)); link(bn + 'S.Result', bn + 'Q.Angle')
            add('RigUnit_GetTransform', bn + 'Xf', RX2 + 1750, RY2 + 3000 + (0 if bone == 'Spine' else 300), Item='(Type=Bone,Name="%s")' % bone, Space='GlobalSpace')
            add('RigUnit_MathQuaternionMul', bn + 'Rot', RX2 + 2250, RY2 + 2900 + (0 if bone == 'Spine' else 300)); link(bn + 'Q.Result', bn + 'Rot.A'); link(bn + 'Xf.Transform.Rotation', bn + 'Rot.B')
            add('RigUnit_SetRotation', bn + 'Set', RX2 + 2500, RY2 + 2900 + (0 if bone == 'Spine' else 300), Item='(Type=Bone,Name="%s")' % bone, Space='GlobalSpace', bPropagateToChildren='True')
            link(bn + 'Rot.Result', bn + 'Set.Value')
            prev = chain_exec(prev, bn + 'Set')
        # rappel / zipline (2026-11-15; curve 'Zip' from ABP_Furina = FurinaZip flag, set while the Grind component's UsingZipline? is true):
        # the left arm is left to the bundle's one-handed zipline animation (hand overhead on the handle, IK weight 1 - Zip), the right wrist goes
        # to a one-handed rifle carry at the right hip (mesh space, cm) so the rifle hangs from one hand
        add('RigUnit_GetCurveValue', 'ZipC', RX2 - 250, RY2 + 2150, Curve='Zip')
        add('RigUnit_AccumulateFloatLerp', 'ZipW', RX2, RY2 + 2150, Blend='8', bIntegrateDeltaTime='True')
        link('ZipC.Value', 'ZipW.TargetValue')
        add('RigUnit_MathFloatRemap', 'ZipInv', RX2 + 250, RY2 + 2150, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True')
        link('ZipW.Result', 'ZipInv.Value')
        for side, toff, qoff, pole, y0 in (('Right', None, FR['q_r'], (-1.0, 0.0, -1.5), RY2 + 1000), ('Left', 'LHandOff3.Result', FR['q_l'], (1.0, 0.0, -1.5), RY2 + 1400)):
            s = 'R' + side[0]
            add('RigUnit_MathQuaternionRotateVector', s + 'HOff', RX2 + 1500, y0, Vector=V(*FR['t_r']) if side == 'Right' else V(0, 0, 0))
            link('GRotR.Result', s + 'HOff.Transform')
            if toff: link(toff, s + 'HOff.Vector')
            add('RigUnit_MathVectorAdd', s + 'HPos', RX2 + 1750, y0)
            link('GPosR.Result', s + 'HPos.A'); link(s + 'HOff.Result', s + 'HPos.B')
            add('RigUnit_MathQuaternionMul', s + 'HRot', RX2 + 1750, y0 + 150, B=Q(qoff))
            link('GRotR.Result', s + 'HRot.A')
            add('RigUnit_TwoBoneIKSimplePerItem', s + 'ArmIK', RX2 + 2050, y0,
                ItemA='(Type=Bone,Name="%s-arm")' % side, ItemB='(Type=Bone,Name="%s-elbow")' % side, EffectorItem='(Type=Bone,Name="%s-wrist")' % side,
                PrimaryAxis=V(0, -1, 0), SecondaryAxis=V(0, 0, 1), SecondaryAxisWeight='0', PoleVectorKind='Direction', PoleVector=V(*pole),
                bPropagateToChildren='True', ItemALength='21.14', ItemBLength='18.02')
            hpos = s + 'HPos.Result'
            if side == 'Right':
                add('RigUnit_MathVectorLerp', 'RRHPosZip', RX2 + 1900, y0 + 80, B=V(*PO.get('zip_right_hand', (-22.0, 28.0, 100.0))))
                link('RRHPos.Result', 'RRHPosZip.A'); link('ZipW.Result', 'RRHPosZip.T'); hpos = 'RRHPosZip.Result'
            hrot = s + 'HRot.Result'
            if side == 'Left':
                # zipline / rappel (2026-11-15 b): the left arm is no longer left to the bundle's animation (the vertical / uphill ziplines play the TWO-handed clips, and the one-handed clip has the elbow
                # flared out at ~33 cm). While riding (ZipW) the left hand goes to a point straight above the left shoulder (poses.zip_left_hand_off, default (0, 9, 37.5) cm: 38.6 cm of the 39.2 cm arm =
                # almost fully extended) and keeps the animation's wrist rotation; the right hand carries the rifle at the hip (RRHPosZip below). IK weight stays 1.
                add('RigUnit_GetTransform', 'LZArmXf', RX2 + 1750, y0 + 500, Item='(Type=Bone,Name="Left-arm")', Space='GlobalSpace')
                add('RigUnit_MathVectorAdd', 'LZipPos', RX2 + 1900, y0 + 500, B=V(*PO.get('zip_left_hand_off', (0.0, 9.0, 37.5)))); link('LZArmXf.Transform.Translation', 'LZipPos.A')
                add('RigUnit_MathVectorLerp', 'LHPosZip', RX2 + 1900, y0 + 600); link(s + 'HPos.Result', 'LHPosZip.A'); link('LZipPos.Result', 'LHPosZip.B'); link('ZipW.Result', 'LHPosZip.T'); hpos = 'LHPosZip.Result'
                add('RigUnit_GetTransform', 'LZWrXf', RX2 + 1750, y0 + 700, Item='(Type=Bone,Name="Left-wrist")', Space='GlobalSpace')
                add('RigUnit_MathQuaternionSlerp', 'LHRotZip', RX2 + 1900, y0 + 700); link(s + 'HRot.Result', 'LHRotZip.A'); link('LZWrXf.Transform.Rotation', 'LHRotZip.B'); link('ZipW.Result', 'LHRotZip.T'); hrot = 'LHRotZip.Result'
            link(hpos, s + 'ArmIK.Effector.Translation'); link(hrot, s + 'ArmIK.Effector.Rotation')
            if side == 'Left':
                # reach compensation (2026-11-15): the grip target sits at / beyond the 39.2 cm arm length (FP hip pose 38.4-42 cm), so the walking / idle body animation moved the shoulder
                # in and out of reach and the supporting hand slid along the handguard ("shaking", walk probe: wrist in rifle space std 2.7 cm along the barrel). The left shoulder joint is
                # now pulled toward the target by whatever exceeds poses.left_reach_max (default 37 cm) - shoulder + children move rigidly, so the IK always has slack and the hand stays on the gun.
                RMAX = PO.get('left_reach_max', 37.0)
                add('RigUnit_GetTransform', 'LShXf', RX2 + 1750, y0 + 300, Item='(Type=Bone,Name="Left-arm")', Space='GlobalSpace')
                add('RigUnit_MathVectorSub', 'LShD', RX2 + 2000, y0 + 300); link(s + 'HPos.Result', 'LShD.A'); link('LShXf.Transform.Translation', 'LShD.B')
                add('RigUnit_MathVectorLength', 'LShLen', RX2 + 2200, y0 + 300); link('LShD.Result', 'LShLen.Value')
                add('RigUnit_MathFloatSub', 'LShOver0', RX2 + 2400, y0 + 300, B=str(RMAX)); link('LShLen.Result', 'LShOver0.A')
                add('RigUnit_MathFloatMax', 'LShOver', RX2 + 2600, y0 + 300, B='0'); link('LShOver0.Result', 'LShOver.A')
                add('RigUnit_MathFloatMul', 'LShOverW', RX2 + 2800, y0 + 300); link('LShOver.Result', 'LShOverW.A'); link('ZipInv.Result', 'LShOverW.B')
                add('RigUnit_MathFloatDiv', 'LShFrac', RX2 + 3000, y0 + 300); link('LShOverW.Result', 'LShFrac.A'); link('LShLen.Result', 'LShFrac.B')
                add('RigUnit_MathVectorScale', 'LShMove', RX2 + 3200, y0 + 300); link('LShD.Result', 'LShMove.Value'); link('LShFrac.Result', 'LShMove.Factor')
                add('RigUnit_MathVectorAdd', 'LShNew', RX2 + 3400, y0 + 300); link('LShXf.Transform.Translation', 'LShNew.A'); link('LShMove.Result', 'LShNew.B')
                add('RigUnit_SetTranslation', 'LShSet', RX2 + 3600, y0 + 300, Item='(Type=Bone,Name="Left-arm")', Space='GlobalSpace', bPropagateToChildren='True'); link('LShNew.Result', 'LShSet.Value')
                prev = chain_exec(prev, 'LShSet')
            prev = chain_exec(prev, s + 'ArmIK')
        # ---- first person: the four left-hand fingers wrap around the handguard (2026-11-16). fp_rig.json 'fingers_l' = {bone: {axis: bone-local unit axis, deg}} from Scripts/Tools/fit_finger_curl.py
        # (measured finger joints ran through the handguard). Local additive rotation (RigUnit_AddBoneTransform, post multiply), weight = first person x not reloading x not on the zipline.
        if FR.get('fingers_l'):
            add('RigUnit_MathFloatRemap', 'FingFp', RX2 + 3900, RY2 + 1400, SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True'); link('ViewTPC.Value', 'FingFp.Value')
            add('RigUnit_MathFloatMul', 'FingW1', RX2 + 4100, RY2 + 1400); link('FingFp.Result', 'FingW1.A'); link('NotReload.Result', 'FingW1.B')
            add('RigUnit_MathFloatMul', 'FingW', RX2 + 4300, RY2 + 1400); link('FingW1.Result', 'FingW.A'); link('ZipInv.Result', 'FingW.B')
            for fi, (bone, fv) in enumerate(FR['fingers_l'].items()):
                ax = fv['axis']; th = math.radians(fv['deg'] * FR.get('fingers_l_scale', 1.0)); sn = math.sin(th / 2); q = (ax[0] * sn, ax[1] * sn, ax[2] * sn, math.cos(th / 2))
                nm = 'Fing_' + bone; bk = '(Type=Bone,Name="%s")' % bone
                # explicit local-space version of "local_new = local_anim * delta": GetTransform(Local) -> quaternion mul -> SetRotation(Local, weight)
                add('RigUnit_GetTransform', nm + 'Get', RX2 + 4500, RY2 + 1400 + 200 * fi, Item=bk, Space='LocalSpace')
                add('RigUnit_MathQuaternionMul', nm + 'Mul', RX2 + 4750, RY2 + 1400 + 200 * fi, B='(X=%f,Y=%f,Z=%f,W=%f)' % q); link(nm + 'Get.Transform.Rotation', nm + 'Mul.A')
                add('RigUnit_SetRotation', nm, RX2 + 5000, RY2 + 1400 + 200 * fi, Item=bk, Space='LocalSpace', bPropagateToChildren='True'); link(nm + 'Mul.Result', nm + '.Value')
                link('FingW.Result', nm + '.Weight')
                prev = chain_exec(prev, nm)

    # ---------------- hair: actual component travel, independent of animated hip/head bob.
    # A filtered 0..1 signal owns amplitude, backward trail, and phase speed. The
    # old whole-chain physics is disabled so it cannot fight this bounded motion.
    add('RigUnit_ToWorldSpace_Location', 'HairWorldOrigin', -1800, -5900, Value=V(0, 0, 0))
    add('RigUnit_DeltaFromPreviousVector', 'HairTravel', -1550, -5900)
    link('HairWorldOrigin.World', 'HairTravel.Value')
    add('RigUnit_MathVectorMul', 'HairTravelXY', -1300, -5900, B=V(1, 1, 0))
    link('HairTravel.Delta', 'HairTravelXY.A')
    add('RigUnit_MathVectorLength', 'HairDistance', -1050, -5900)
    link('HairTravelXY.Result', 'HairDistance.Value')
    add('RigUnit_MathFloatDiv', 'HairSpeedRaw', -800, -5900)
    link('HairDistance.Result', 'HairSpeedRaw.A'); link('DtSafe.Result', 'HairSpeedRaw.B')
    add('RigUnit_MathFloatRemap', 'HairSpeedRatio', -550, -5900, SourceMinimum='6', SourceMaximum=str(P['sprint']), TargetMinimum='0', TargetMaximum='1', bClamp='True')
    link('HairSpeedRaw.Result', 'HairSpeedRatio.Value')
    add('RigUnit_AccumulateFloatLerp', 'HairFlow', -300, -5900, Blend=str(P.get('hair_speed_blend', 3.8)), bIntegrateDeltaTime='True')
    link('HairSpeedRatio.Result', 'HairFlow.TargetValue')
    add('RigUnit_MathFloatMul', 'HairTempoRun', -50, -5900, B='0.9')
    link('HairFlow.Result', 'HairTempoRun.A')
    add('RigUnit_MathFloatAdd', 'HairTempo', 200, -5900, B='1')
    link('HairTempoRun.Result', 'HairTempo.A')
    add('RigUnit_SetCurveValue', 'SetHairFlow', -1800, -5500, Curve='HairFlow')
    link('HairFlow.Result', 'SetHairFlow.Value')
    prev = chain_exec(prev, 'SetHairFlow')
    add('RigUnit_SetCurveValue', 'SetHairDyn', -1550, -5200, Curve='HairDyn', Value='0')
    prev = chain_exec(prev, 'SetHairDyn')
    add('RigUnit_SetCurveValue', 'SetAhogeDyn', -1550, -5000, Curve='AhogeDyn', Value='0')
    prev = chain_exec(prev, 'SetAhogeDyn')
    for cv, src, x in (('DbgL', 'LD.Result', 0), ('DbgR', 'RD.Result', 1), ('DbgW', 'SlopeW.Result', 2), ('DbgC', 'Run.Result', 3)):
        add('RigUnit_SetCurveValue', 'Set' + cv, -1300 + x * 250, -5200, Curve=cv)
        link(src, 'Set%s.Value' % cv)
        prev = chain_exec(prev, 'Set' + cv)

    y = 0
    for i, ch in enumerate(P['chains']):
        n = 'C%02d' % i
        x0 = 700 + (i % 4) * 1500; y = (i // 4) * 900
        # backward lift about the component right axis, proportional to the (sprung) drive
        if ch['lift'] > 0:
            add('RigUnit_GetTransform', n + 'Root', x0, y, Item='(Type=Bone,Name="%s")' % ch['root'], Space='GlobalSpace')
            # negative angle about +X swings a hanging strand toward -Y (behind Furina)
            add('RigUnit_MathFloatMul', n + 'AngT', x0, y + 200, B=str(-math.radians(ch['lift']) / (2.0 if ch['kind'] == 'cloth' else 1.0)))
            link('TrailC.Result' if ch['kind'] == 'cloth' else 'HairFlow.Result', n + 'AngT.A')
            add('RigUnit_MathFloatMul', n + 'AngB', x0, y + 350, B=str(-math.radians(ch.get('bob', 0))))
            link('Bob.Result', n + 'AngB.A')
            add('RigUnit_MathFloatMul', n + 'AngBR', x0 + 120, y + 350)      # bounce only while moving
            link(n + 'AngB.Result', n + 'AngBR.A'); link('Move.Result', n + 'AngBR.B')
            add('RigUnit_MathFloatAdd', n + 'Ang', x0 + 250, y + 300)
            link(n + 'AngT.Result', n + 'Ang.A'); link(n + 'AngBR.Result', n + 'Ang.B')
            add('RigUnit_MathQuaternionFromAxisAndAngle', n + 'Q', x0 + 250, y + 200, Axis=V(1, 0, 0))
            link(n + 'Ang.Result', n + 'Q.Angle')
            add('RigUnit_MathQuaternionMul', n + 'Rot', x0 + 500, y + 100)
            link(n + 'Q.Result', n + 'Rot.A'); link(n + 'Root.Transform.Rotation', n + 'Rot.B')
            add('RigUnit_SetRotation', n + 'Lift', x0 + 750, y, Item='(Type=Bone,Name="%s")' % ch['root'], Space='GlobalSpace', bPropagateToChildren='True')
            link(n + 'Rot.Result', n + 'Lift.Value')
            prev = chain_exec(prev, n + 'Lift')
        # travelling wave along the chain: amplitude and tempo follow speed (+ idle breeze for hair)
        if not ch.get('wave', True): continue
        a = ch['amp']; b = ch['idle']
        add('RigUnit_MathVectorScale', n + 'AmpS', x0 + 750, y + 300, Value=V(a[0], 0, a[1]))
        link('Run.Result' if ch['kind'] == 'cloth' else 'HairFlow.Result', n + 'AmpS.Factor')
        add('RigUnit_MathVectorAdd', n + 'Amp', x0 + 1000, y + 300, B=V(b[0], 0, b[1]))
        link(n + 'AmpS.Result', n + 'Amp.A')
        add('RigUnit_MathVectorScale', n + 'Spd', x0 + 1000, y + 450, Value=V(ch['tempo'], ch['tempo'], ch['tempo'] * 1.3))
        link('Tempo.Result' if ch['kind'] == 'cloth' else 'HairTempo.Result', n + 'Spd.Factor')
        add('RigUnit_ChainHarmonicsPerItem', n + 'Wave', x0 + 1250, y,
            ChainRoot='(Type=Bone,Name="%s")' % ch['root'], bDrawDebug='False',
            Wave='(bEnabled=True,WaveFrequency=%s,WaveAmplitude=%s,WaveOffset=%s,WaveNoise=(X=0,Y=0,Z=0),WaveMinimum=%f,WaveMaximum=1.0,WaveEase=Linear)' % (
                V(ch['spatial'], 0, ch['spatial'] * .8), V(0, 0, 0), V(ch['phase'], 0, ch['phase'] + 1.3), ch['rootAmp']))
        if ch['kind'] == 'hair':
            # The unit's default 0..1 curve multiplies the taper a second time,
            # completely pinning the root of the two-bone side strands. Use one
            # explicit taper, so short strands also receive a small breeze.
            if not c.set_pin_default_value(n + 'Wave.WaveCurve',
                    '(EditorCurveData=(Keys=((Time=0.000000,Value=1.000000),(Time=1.000000,Value=1.000000))))', True, False):
                res['fail'].append('hair wave curve ' + n)
            pd = ch.get('pend')
            if pd:
                # every joint lags behind its rest direction (follow-through) -> silky ripple instead of a rigid strand.
                # UnwindAxis must be perpendicular to the bone length axis (Y for these bones).
                ptxt = ('(bEnabled=True,PendulumStiffness=%f,PendulumGravity=(X=0,Y=0,Z=%f),PendulumBlend=%f,PendulumDrag=%f,'
                        'PendulumMinimum=%f,PendulumMaximum=%f,PendulumEase=Linear,UnwindAxis=(X=1,Y=0,Z=0),UnwindMinimum=0.2,UnwindMaximum=0.05)') % (
                    pd['stiff'], pd['grav'], pd['blend'], pd['drag'], pd['min'], pd['max'])
                if not c.set_pin_default_value(n + 'Wave.Pendulum', ptxt, True, False):
                    res['fail'].append('hair pendulum ' + n)
        link(n + 'Amp.Result', n + 'Wave.Wave.WaveAmplitude')
        link(n + 'Spd.Result', n + 'Wave.Speed')
        prev = chain_exec(prev, n + 'Wave')
    # ---------------- Unity blink timing: independent of locomotion curve weights.
    # Every 4-5 s, close .045 s / hold .065 s / open .085 s, IdleBlink morph 0..1.
    by = 4200
    add('RigUnit_TimeLoop', 'BlinkLoop', -1800, by, Speed='1', Duration='4.5', Normalize='False')
    add('RigUnit_MathFloatMul', 'BlinkJt', -1550, by + 200, B='0.37')
    link('BlinkLoop.Absolute', 'BlinkJt.A')
    add('RigUnit_MathFloatSin', 'BlinkJs', -1350, by + 200)
    link('BlinkJt.Result', 'BlinkJs.Value')
    add('RigUnit_MathFloatMul', 'BlinkJ', -1150, by + 200, B='0.25')          # start jitter -> 4..5 s intervals
    link('BlinkJs.Result', 'BlinkJ.A')
    add('RigUnit_MathFloatAdd', 'BlinkStart', -950, by + 200, B='2.25')
    link('BlinkJ.Result', 'BlinkStart.A')
    add('RigUnit_MathFloatSub', 'BlinkLocal', -750, by)
    link('BlinkLoop.Relative', 'BlinkLocal.A'); link('BlinkStart.Result', 'BlinkLocal.B')
    add('RigUnit_MathFloatDiv', 'BlinkUpR', -550, by - 100, B='0.045')
    link('BlinkLocal.Result', 'BlinkUpR.A')
    add('RigUnit_MathFloatClamp', 'BlinkUp', -350, by - 100, Minimum='0', Maximum='1')
    link('BlinkUpR.Result', 'BlinkUp.Value')
    add('RigUnit_MathFloatSub', 'BlinkDnS', -550, by + 100, A='0.195')
    link('BlinkLocal.Result', 'BlinkDnS.B')
    add('RigUnit_MathFloatDiv', 'BlinkDnR', -350, by + 100, B='0.085')
    link('BlinkDnS.Result', 'BlinkDnR.A')
    add('RigUnit_MathFloatClamp', 'BlinkDn', -150, by + 100, Minimum='0', Maximum='1')
    link('BlinkDnR.Result', 'BlinkDn.Value')
    add('RigUnit_MathFloatMin', 'BlinkW', 50, by)
    link('BlinkUp.Result', 'BlinkW.A'); link('BlinkDn.Result', 'BlinkW.B')
    add('RigUnit_MathFloatMul', 'BlinkS1', 250, by + 100, B='-2')                # smoothstep w*w*(3-2w)
    link('BlinkW.Result', 'BlinkS1.A')
    add('RigUnit_MathFloatAdd', 'BlinkS2', 450, by + 100, B='3')
    link('BlinkS1.Result', 'BlinkS2.A')
    add('RigUnit_MathFloatMul', 'BlinkS3', 650, by)
    link('BlinkS2.Result', 'BlinkS3.A'); link('BlinkW.Result', 'BlinkS3.B')
    add('RigUnit_MathFloatMul', 'BlinkS4', 850, by)
    link('BlinkS3.Result', 'BlinkS4.A'); link('BlinkW.Result', 'BlinkS4.B')
    add('RigUnit_GetCurveValue', 'IdleCurve', 450, by + 400, Curve='FurinaIdle')
    add('RigUnit_MathFloatRemap', 'IdleGate', 650, by + 400, SourceMinimum='0.9', SourceMaximum='1', TargetMinimum='0', TargetMaximum='1', bClamp='True')
    link('IdleCurve.Value', 'IdleGate.Value')
    add('RigUnit_MathFloatMul', 'BlinkOut', 1050, by, B='1')
    link('BlinkS4.Result', 'BlinkOut.A')
    add('RigUnit_SetCurveValue', 'SetBlink', 1300, by, Curve='IdleBlink')
    link('BlinkOut.Result', 'SetBlink.Value')
    prev = chain_exec(prev, 'SetBlink')
    log('timeloop', getattr(unreal, 'RigUnit_TimeLoop')().export_text())
    bp.set_auto_vm_recompile(True)
    bp.recompile_vm()
    res['status'] = str(bp.get_editor_property('status')) if True else None
    skeleton = unreal.load_asset('/Game/Furina/SK_Furina_Skeleton')
    unreal.AnimationLibrary.set_curve_meta_data_morph_target(skeleton, 'IdleBlink', True)
    if not STAGE_ONLY:
        assert eal.save_loaded_asset(skeleton, False)
        assert eal.save_loaded_asset(bp, False)   # NOTE: nothing is saved while Data/hair_stage_only exists (STAGE_ONLY) - then run ue_force_save_cr.py after the build
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_build_cr.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('BUILD_CR_DONE')

