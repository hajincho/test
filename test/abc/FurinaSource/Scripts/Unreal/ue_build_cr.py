"""Builds /Game/Furina/CR_FurinaSecondary: speed-proportional cloth flapping + hair motion (Unity FurinaHairRig chains)."""
import unreal, json, traceback, os, math
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
P = json.load(open(os.path.join(S, 'cr_params.json'), encoding='utf-8'))
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
    for cv in ('IdleBlink', 'FurinaIdle', 'HairDyn', 'AhogeDyn', 'HairFlow', 'DbgL', 'DbgR', 'DbgW', 'DbgC'):
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
    link('HipsXf.Transform.Translation', 'HipsWorld.Value')
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
    add('RigUnit_MathFloatAdd', 'IKWa', LX + 2250, LY + 550)
    link('SlopeW.Result', 'IKWa.A'); link('Run.Result', 'IKWa.B')
    add('RigUnit_MathFloatMul', 'IKWs', LX + 2500, LY + 550, B='1')
    link('IKWa.Result', 'IKWs.A')
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
        link('Run.Result', s + 'Narrow.A'); link(s + 'Narrow.Result', s + 'LiftV.X')
        # sprint only: shorter fore-aft split (foot Y relative to the hips) and a lower heel kick
        add('RigUnit_MathFloatSub', s + 'FY', X2, y0 + 380)
        link(s + 'Ank.Transform.Translation.Y', s + 'FY.A'); link('HipsXf.Transform.Translation.Y', s + 'FY.B')
        add('RigUnit_MathFloatMul', s + 'FYs', X2 + 120, y0 + 380, B=str(P.get('run_stride', 0.72) - 1.0))
        link(s + 'FY.Result', s + 'FYs.A')
        add('RigUnit_MathFloatMul', s + 'FYr', X2 + 250, y0 + 380)
        link(s + 'FYs.Result', s + 'FYr.A'); link('Run.Result', s + 'FYr.B')
        link(s + 'FYr.Result', s + 'LiftV.Y')
        add('RigUnit_MathFloatSub', s + 'FZ', X2, y0 + 480, B='10')
        link(s + 'Ank.Transform.Translation.Z', s + 'FZ.A')
        add('RigUnit_MathFloatMul', s + 'FZs', X2 + 120, y0 + 480, B=str(P.get('run_kick', 0.7) - 1.0))
        link(s + 'FZ.Result', s + 'FZs.A')
        add('RigUnit_MathFloatMul', s + 'FZr', X2 + 250, y0 + 480)
        link(s + 'FZs.Result', s + 'FZr.A'); link('Run.Result', s + 'FZr.B')
        add('RigUnit_MathFloatAdd', s + 'LiftZ', X2 + 380, y0 + 230)
        link(s + 'LiftW.Result', s + 'LiftZ.A'); link(s + 'FZr.Result', s + 'LiftZ.B')
        link(s + 'LiftZ.Result', s + 'LiftV.Z')
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
    add('RigUnit_MathVectorMake', 'DropV', LX + 2750, LY + 350, X='0', Y='0')
    add('RigUnit_MathFloatMul', 'DropVZ', LX + 2600, LY + 450, B='-1')
    link('DropW.Result', 'DropVZ.A'); link('DropVZ.Result', 'DropV.Z')
    add('RigUnit_MathVectorAdd', 'HipsLow', LX + 3000, LY + 350)
    link('HipsXf.Transform.Translation', 'HipsLow.A'); link('DropV.Result', 'HipsLow.B')
    add('RigUnit_SetTranslation', 'HipsDrop', LX + 3250, LY + 350, Item='(Type=Bone,Name="Hips")', Space='GlobalSpace', bPropagateToChildren='True')
    link('HipsLow.Result', 'HipsDrop.Value')
    prev = chain_exec(prev, 'HipsDrop')

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
        assert eal.save_asset(DEST)
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_build_cr.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('BUILD_CR_DONE')

