"""ABP_Furina graph v4 = v3 + Unity walk blend (FurinaWalk) + hair angular springs / HairDyn alpha. v3 = v2 (retarget + old idle -> CR_FurinaSecondary) + Unity hair chain physics (AnimDynamics).
Hair parameters follow HuTaoChainPhysics.ProfileFor() (Furina naming): HairBack (braids), HairSide (CF), Ahoge (DM).
Body capsules follow HuTaoChainPhysics.CacheBodyCapsules() for Furina; initial contacts are excluded like
CacheAttachmentContacts() by shrinking a sphere until no rest joint of that chain starts inside it."""
import json, math, sys, uuid
D = sys.argv[1]
ref = json.load(open(D + r'\ue_ref.json', encoding='utf-8'))
pl = json.load(open(D + r'\furina_player.json', encoding='utf-8'))
parent = {}
for n in pl['nodes'].values():
    if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/'):
        p = pl['nodes'].get(n['parent'])
        parent[n['name'].replace(' ', '-')] = p['name'].replace(' ', '-') if p and p['name'] != 'Armature' else None
children = {}
for c, p in parent.items(): children.setdefault(p, []).append(c)

def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v):
    p = qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3])); return p[:3]
G = {}
def glob(b):
    if b in G: return G[b]
    p = parent.get(b); lp = ref[b]['p']; lq = tuple(ref[b]['q'])
    if p is None: G[b] = (tuple(lp), lq)
    else:
        pp, pq = glob(p); G[b] = (tuple(a + c for a, c in zip(pp, qrot(pq, lp))), qmul(pq, lq))
    return G[b]
def chain(root):
    out = [root]
    while children.get(out[-1]):
        nxt = [c for c in children[out[-1]] if c.split('_')[0] == root.split('_')[0]]
        if not nxt: break
        out.append(nxt[0])
    return out

PROFILES = {  # HuTaoChainPhysics.ProfileFor
    'HairBack': dict(stiff=(7, 2.4), damp=(5.8, 3.4), grav=(.12, .42), limit=(22, 68), rad=(.010, .016), acc=(.20, .80), vel=(.06, .26)),
    'HairSide': dict(stiff=(10, 4), damp=(6, 4), grav=(.10, .34), limit=(18, 50), rad=(.008, .012), acc=(.15, .55), vel=(.05, .20)),
    'Ahoge': dict(stiff=(16, 7), damp=(3.2, 2.1), grav=(.02, .07), limit=(12, 42), rad=(.005, .007), acc=(.30, 1.0), vel=(.03, .12)),
}
CHAINS = [('F_0_1_L', 'HairBack'), ('F_0_1_R', 'HairBack'), ('CF_1_L', 'HairSide'), ('CF_1_R', 'HairSide'), ('DM_0_1', 'Ahoge')]
CAPS = [('Hips', 'Chest', 11.5), ('Chest', 'Neck', 9.5), ('Neck', 'Head', 5.0), ('Head', 'DM_0_1', 8.0)]
for s in ('Left', 'Right'):
    CAPS += [(s + '-shoulder', s + '-arm', 5.0), (s + '-arm', s + '-elbow', 4.5)]

def lerp(a, b, t): return a + (b - a) * t
def dist(a, b): return math.dist(a, b)
report = []
def V(x, y, z): return '(X=%.4f,Y=%.4f,Z=%.4f)' % (x, y, z)

def qinv(q): return (-q[0], -q[1], -q[2], q[3])
# Unity stiffness pulls every joint back toward its rest shape. In AnimDynamics the *linear* spring instead pulls each
# body onto the previous joint, which straightens the whole chain along its root direction (measured: braids stuck out
# 80-90 cm sideways). So: no linear spring; an angular spring aims each body's bone axis at its rest direction, and\n# the root body at its animated bone.\n# UE 5.8 BoneRelative sim space converts world vectors with ComponentTransform * Bone (wrong order, AnimNode_AnimDynamics.cpp\n# TransformWorldVectorToSimSpace) -> gravity and headwind point sideways. So simulate in Component space instead.
ANG_SPRING = {'HairBack': 150.0, 'HairSide': 300.0, 'Ahoge': 800.0}
HEADWIND = {'HairBack': 0.6, 'HairSide': 0.20, 'Ahoge': 0.08}
# the ahoge reacted to every idle head bob (1.3 cm rms while standing): follow body acceleration much less
ACC_MUL = {'HairBack': 1.0, 'HairSide': 1.0, 'Ahoge': 0.3}
def anim_dynamics(root, kind):
    pr = PROFILES[kind]; bones = chain(root); n = len(bones)
    pos = [glob(b)[0] for b in bones]
    # bone length axis from the first child offset
    off = ref[bones[1]]['p'] if n > 1 else [0, 1, 0]
    ax = max(range(3), key=lambda i: abs(off[i])); twist = 'Axis' + 'XYZ'[ax]
    unit = [0, 0, 0]; unit[ax] = 1.0
    hq = glob('Head')[1]
    bodies = []
    for i, b in enumerate(bones):
        t = i / max(1, n - 1)
        L = lerp(*pr['limit'], t); r = lerp(*pr['rad'], t) * 100
        # limits are measured from the parent body's frame (identity), but the rest pose is already bent by the
        # bone's local rotation: widen the swing range by that rest bend so the rest shape sits well inside it
        rest = 0.0 if i == 0 else math.degrees(2 * math.acos(min(1.0, abs(ref[b]['q'][3]))))
        Ls = L + rest
        lim = [Ls, Ls, Ls]; lim[ax] = min(10.0, L * .3) + rest
        if i == 0: tgt = tuple(unit)                                       # root: follow the animated bone
        else: tgt = qrot(glob(b)[1], unit)                                 # rest bone axis in component space (= sim space)
        bodies.append('(BoundBone=(BoneName="%s"),BoxExtents=(X=%.2f,Y=%.2f,Z=%.2f),LocalJointOffset=(X=0,Y=0,Z=0),'
                      'ConstraintSetup=(LinearXLimitType=Limited,LinearYLimitType=Limited,LinearZLimitType=Limited,LinearAxesMin=(X=0,Y=0,Z=0),LinearAxesMax=(X=0,Y=0,Z=0),'
                      'AngularConstraintType=Angular,TwistAxis=%s,AngularTargetAxis=%s,ConeAngle=0,AngularLimitsMin=(X=%.1f,Y=%.1f,Z=%.1f),AngularLimitsMax=(X=%.1f,Y=%.1f,Z=%.1f),AngularTarget=%s),'
                      'CollisionType=CustomSphere,SphereCollisionRadius=%.2f)' % (b, r * 2, r * 2, r * 2, twist, twist, -lim[0], -lim[1], -lim[2], lim[0], lim[1], lim[2], V(*tgt), r))
    # body capsules as spheres along each segment; skip/shrink any sphere a rest joint already touches
    spheres = []
    for a, b, rad in CAPS:
        if a not in ref or b not in ref: continue
        pa, qa = glob(a); pb = glob(b)[0]
        for f in (.25, .5, .75):
            c = tuple(x + (y - x) * f for x, y in zip(pa, pb))
            free = min(dist(c, p) - lerp(*pr['rad'], i / max(1, n - 1)) * 100 for i, p in enumerate(pos) if i > 0)
            r = min(rad, free - .5)
            if r < 1.0: continue
            local = qrot((-qa[0], -qa[1], -qa[2], qa[3]), tuple(x - y for x, y in zip(c, pa)))
            spheres.append('(DrivingBone=(BoneName="%s"),SphereLocalOffset=%s,LimitRadius=%.2f,LimitType=Outer)' % (a, V(*local), r))
    stiff = sum(pr['stiff']) / 2; grav = sum(pr['grav']) / 2 * .6; damp = sum(pr['damp']) / 2
    acc = sum(pr['acc']) / 2 * .6 * ACC_MUL[kind]
    # running headwind (speed-proportional). Must beat gravity enough to stream the hair back even though the run pose
    # leans forward: sprint 600 cm/s x .6 = 360 cm/s^2 vs gravity ~160 -> braids trail ~50 deg back at full sprint.
    vel = HEADWIND[kind]
    # Unity: velocity *= exp(-damping*dt)  ->  AnimDynamics: velocity *= (1-d)^dt  =>  d = 1 - exp(-damping)
    dmp = 1 - math.exp(-damp)
    spring = 12 * stiff * stiff
    report.append((root, kind, n, twist, len(spheres), round(spring, 1), round(grav, 3), round(dmp, 3)))
    # Unity parentMotionInfluence (.82 root -> .10 tip): hair rides with the head. Simulate in Head space and pass
    # only part of the head's own motion back in, so pose pops never leave the strands behind.
    report[-1] = report[-1] + (ANG_SPRING[kind],)
    return ('(AlphaInputType=Curve,AlphaCurveName="' + ('AhogeDyn' if kind == 'Ahoge' else 'HairDyn') + '",'
            'BoundBone=(BoneName="%s"),ChainEnd=(BoneName="%s"),bChain=True,PhysicsBodyDefinitions=(%s),SimulationSpace=Component,'
            'GravityScale=%.3f,bLinearSpring=False,bAngularSpring=True,LinearSpringConstant=%.1f,AngularSpringConstant=' + str(ANG_SPRING[kind]) + ','
            'ComponentLinearAccScale=(X=%.2f,Y=%.2f,Z=%.2f),ComponentLinearVelScale=(X=%.2f,Y=%.2f,Z=%.2f),ComponentAppliedLinearAccClamp=(X=800,Y=800,Z=800),'
            'SimSpaceSettings=(SimSpaceAngularAlpha=%.2f,MaxAngularVelocity=20,MaxAngularAcceleration=200,ExternalAngularVelocity=(X=0,Y=0,Z=0)),'
            'bOverrideLinearDamping=True,LinearDampingOverride=%.2f,bOverrideAngularDamping=True,AngularDampingOverride=%.2f,'
            'NumSolverIterationsPreUpdate=8,NumSolverIterationsPostUpdate=2,bUseSphericalLimits=True,SphericalLimits=(%s),bUsePlanarLimit=False)') % (
        bones[0], bones[-1], ','.join(bodies), grav, spring, acc, acc, acc, vel, vel, vel * .5, .3,
        dmp, dmp, ','.join(spheres))

def gid(): return uuid.uuid4().hex.upper()
LINK = "PinType.PinCategory=\"struct\",PinType.PinSubCategory=\"\",PinType.PinSubCategoryObject=\"/Script/CoreUObject.ScriptStruct'/Script/Engine.%s'\",PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False"
def pin(pid, name, struct, out, link=None):
    s = 'CustomProperties Pin (PinId=%s,PinName="%s",' % (pid, name)
    if out: s += 'Direction="EGPD_Output",'
    s += LINK % struct + ','
    if not out: s += 'DefaultValue="(LinkID=-1,SourceLinkID=-1)",AutogeneratedDefaultValue="(LinkID=-1,SourceLinkID=-1)",'
    if link: s += 'LinkedTo=(%s %s,),' % link
    return s + 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)'
RTG = "/Script/IKRig.IKRetargeter'/Game/Furina/Retarget/RTG_Manny_To_Furina.RTG_Manny_To_Furina'"
p = {k: gid() for k in ['ra', 'rb', 'seq', 'twa', 'twb', 'two', 'lbase', 'lb0', 'lout', 'crin', 'crout', 'l2cin', 'l2cout', 'c2lin', 'c2lout',
                        'wseq', 'wa', 'wb', 'wo']}
adp = [(gid(), gid()) for _ in CHAINS]
nodes = [
 # Unity walk (FurinaWalk curve = 1 on Manny's walk anims, 0 on run) replaces the retargeted walk
 ('/Script/IKRigDeveloper.AnimGraphNode_RetargetPoseFromMesh', 'AnimGraphNode_RetargetPoseFromMesh_0', 'Node',
  '(RetargetFrom=ParentSkeletalMeshComponent,IKRetargeterAsset="%s")' % RTG, -1600, -200, [pin(p['ra'], 'Pose', 'PoseLink', True, ('AnimGraphNode_TwoWayBlend_1', p['wa']))]),
 ('/Script/AnimGraph.AnimGraphNode_SequencePlayer', 'AnimGraphNode_SequencePlayer_1', 'Node',
  "(Sequence=\"/Script/Engine.AnimSequence'/Game/Furina/Anim/AS_Furina_Walk.AS_Furina_Walk'\",bLoopAnimation=True)", -1600, 0, [pin(p['wseq'], 'Pose', 'PoseLink', True, ('AnimGraphNode_TwoWayBlend_1', p['wb']))]),
 ('/Script/AnimGraph.AnimGraphNode_TwoWayBlend', 'AnimGraphNode_TwoWayBlend_1', 'BlendNode', '(AlphaInputType=Curve,AlphaCurveName="FurinaWalk")', -1200, -150,
  [pin(p['wa'], 'A', 'PoseLink', False, ('AnimGraphNode_RetargetPoseFromMesh_0', p['ra'])), pin(p['wb'], 'B', 'PoseLink', False, ('AnimGraphNode_SequencePlayer_1', p['wseq'])),
   pin(p['wo'], 'Pose', 'PoseLink', True, ('AnimGraphNode_TwoWayBlend_0', p['twa']))]),
 ('/Script/AnimGraph.AnimGraphNode_SequencePlayer', 'AnimGraphNode_SequencePlayer_0', 'Node',
  "(Sequence=\"/Script/Engine.AnimSequence'/Game/Furina/Anim/AS_Furina_Idle.AS_Furina_Idle'\",bLoopAnimation=True)", -1200, 0, [pin(p['seq'], 'Pose', 'PoseLink', True, ('AnimGraphNode_TwoWayBlend_0', p['twb']))]),
 ('/Script/AnimGraph.AnimGraphNode_TwoWayBlend', 'AnimGraphNode_TwoWayBlend_0', 'BlendNode', '(AlphaInputType=Curve,AlphaCurveName="FurinaIdle")', -800, -100,
  [pin(p['twa'], 'A', 'PoseLink', False, ('AnimGraphNode_TwoWayBlend_1', p['wo'])), pin(p['twb'], 'B', 'PoseLink', False, ('AnimGraphNode_SequencePlayer_0', p['seq'])),
   pin(p['two'], 'Pose', 'PoseLink', True, ('AnimGraphNode_LayeredBoneBlend_0', p['lb0']))]),
 ('/Script/IKRigDeveloper.AnimGraphNode_RetargetPoseFromMesh', 'AnimGraphNode_RetargetPoseFromMesh_1', 'Node',
  '(RetargetFrom=ParentSkeletalMeshComponent,IKRetargeterAsset="%s")' % RTG, -800, -400, [pin(p['rb'], 'Pose', 'PoseLink', True, ('AnimGraphNode_LayeredBoneBlend_0', p['lbase']))]),
 ('/Script/AnimGraph.AnimGraphNode_LayeredBoneBlend', 'AnimGraphNode_LayeredBoneBlend_0', 'Node',
  '(BlendPoses=((LinkID=-1,SourceLinkID=-1)),LayerSetup=((BranchFilters=((BoneName="Hips",BlendDepth=0)))),BlendWeights=(1.000000),CurveBlendOption=UseMaxValue)', -400, -250,
  [pin(p['lbase'], 'BasePose', 'PoseLink', False, ('AnimGraphNode_RetargetPoseFromMesh_1', p['rb'])), pin(p['lb0'], 'BlendPoses_0', 'PoseLink', False, ('AnimGraphNode_TwoWayBlend_0', p['two'])),
   pin(p['lout'], 'Pose', 'PoseLink', True, ('AnimGraphNode_ControlRig_0', p['crin']))]),
 ('/Script/ControlRigDeveloper.AnimGraphNode_ControlRig', 'AnimGraphNode_ControlRig_0', 'Node',
  "(ControlRigAssetReference=(BlueprintRigClass=\"/Script/ControlRigDeveloper.ControlRigBlueprintGeneratedClass'/Game/Furina/CR_FurinaSecondary.CR_FurinaSecondary_C'\"))", 0, -250,
  [pin(p['crin'], 'Source', 'PoseLink', False, ('AnimGraphNode_LayeredBoneBlend_0', p['lout'])), pin(p['crout'], 'Pose', 'PoseLink', True, ('AnimGraphNode_LocalToComponentSpace_0', p['l2cin']))]),
 ('/Script/AnimGraph.AnimGraphNode_LocalToComponentSpace', 'AnimGraphNode_LocalToComponentSpace_0', None, None, 350, -250,
  [pin(p['l2cin'], 'LocalPose', 'PoseLink', False, ('AnimGraphNode_ControlRig_0', p['crout'])), pin(p['l2cout'], 'ComponentPose', 'ComponentSpacePoseLink', True, ('AnimGraphNode_AnimDynamics_0', adp[0][0]))]),
]
for i, (root, kind) in enumerate(CHAINS):
    prev = ('AnimGraphNode_LocalToComponentSpace_0', p['l2cout']) if i == 0 else ('AnimGraphNode_AnimDynamics_%d' % (i - 1), adp[i - 1][1])
    nxt = ('AnimGraphNode_AnimDynamics_%d' % (i + 1), adp[i + 1][0]) if i + 1 < len(CHAINS) else ('AnimGraphNode_ComponentToLocalSpace_0', p['c2lin'])
    nodes.append(('/Script/AnimGraph.AnimGraphNode_AnimDynamics', 'AnimGraphNode_AnimDynamics_%d' % i, 'Node', anim_dynamics(root, kind), 650 + i * 320, -250,
                  [pin(adp[i][0], 'ComponentPose', 'ComponentSpacePoseLink', False, prev), pin(adp[i][1], 'Pose', 'ComponentSpacePoseLink', True, nxt)]))
nodes.append(('/Script/AnimGraph.AnimGraphNode_ComponentToLocalSpace', 'AnimGraphNode_ComponentToLocalSpace_0', None, None, 650 + len(CHAINS) * 320, -250,
              [pin(p['c2lin'], 'ComponentPose', 'ComponentSpacePoseLink', False, ('AnimGraphNode_AnimDynamics_%d' % (len(CHAINS) - 1), adp[-1][1])), pin(p['c2lout'], 'Pose', 'PoseLink', True)]))
out = []
for cls, name, prop, text, x, y, pins in nodes:
    out.append('Begin Object Class=%s Name="%s"' % (cls, name))
    if text: out.append('   %s=%s' % (prop, text))
    out += ['   NodePosX=%d' % x, '   NodePosY=%d' % y, '   NodeGuid=%s' % gid()] + ['   ' + q for q in pins] + ['End Object']
open(D + r'\abp_graph4.t3d', 'w', encoding='utf-8', newline='\r\n').write('\n'.join(out) + '\n')
for r in report: print(r)
