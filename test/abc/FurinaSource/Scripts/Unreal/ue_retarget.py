import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
OUT = os.path.join(S, "ue_retarget.json")
DEST = "/Game/Furina/Retarget"
MANNY = "/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Meshes/Manny_Simple_SK"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def get_or_create(name, cls, factory):
    p = DEST + '/' + name
    if eal.does_asset_exist(p): return unreal.load_asset(p), False
    return tools.create_asset(name, DEST, cls, factory), True

def call(obj, name, *args):
    try:
        r = getattr(obj, name)(*args); log('OK', name, args, '->', r); return r
    except Exception as e:
        log('FAIL', name, args, repr(e)); return None

try:
    for n in ('IK_Furina', 'RTG_Manny_To_Furina'):
        if eal.does_asset_exist(DEST + '/' + n): eal.delete_asset(DEST + '/' + n)
    manny = unreal.load_asset(MANNY)
    furina = unreal.load_asset('/Game/Furina/SK_Furina')
    fpose = furina.get_editor_property('skeleton').get_reference_pose()
    fnames = [str(n) for n in unreal.AnimPoseExtensions.get_bone_names(fpose)]
    norm = {n.replace(' ', '').replace('_', '').replace('-', '').lower(): n for n in fnames}
    def B(n): return norm.get(n.replace(' ', '').replace('_', '').replace('-', '').lower(), n)
    res['furina_bones_sample'] = [n for n in fnames if not n.startswith(('HB', 'F_', 'Bone'))]
    ws = unreal.AnimPoseSpaces.WORLD
    res['furina_ref'] = {n: str(unreal.AnimPoseExtensions.get_bone_pose(fpose, B(n), ws).translation) for n in ['Hips', 'Head', 'Left ankle', 'Left toe', 'Left wrist']}
    mpose = manny.get_editor_property('skeleton').get_reference_pose()
    res['manny_ref'] = {n: str(unreal.AnimPoseExtensions.get_bone_pose(mpose, n, ws).translation) for n in ['pelvis', 'head', 'foot_l', 'ball_l', 'hand_l']}
    # ---------- source rig (mannequin), auto characterized
    src, new = get_or_create('IK_Manny', unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    sc = unreal.IKRigController.get_controller(src)
    res['rig_ctrl_methods'] = [m for m in dir(sc) if not m.startswith('_')]
    if new:
        call(sc, 'set_skeletal_mesh', manny)
        call(sc, 'apply_auto_generated_retarget_definition')
        call(sc, 'apply_auto_fbik')
    chains = []
    for c in sc.get_retarget_chains():
        chains.append(dict(name=str(c.get_editor_property('chain_name')), start=str(c.get_editor_property('start_bone').get_editor_property('bone_name')),
                           end=str(c.get_editor_property('end_bone').get_editor_property('bone_name')), goal=str(c.get_editor_property('ik_goal_name'))))
    res['manny_chains'] = chains
    res['manny_root'] = str(sc.get_retarget_root())
    eal.save_asset(DEST + '/IK_Manny')

    # ---------- target rig (Furina): only Furina's own body joints
    tgt, new = get_or_create('IK_Furina', unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    tc = unreal.IKRigController.get_controller(tgt)
    if new:
        call(tc, 'set_skeletal_mesh', furina)
        call(tc, 'set_retarget_root', B('Hips'))
        manny_names = {c['name'].lower(): c for c in chains}
        def mend(n): return manny_names.get(n.lower(), {}).get('end', '')
        spec = [('Spine', 'Spine', 'Chest', None), ('Neck', 'Neck', 'Neck', None), ('Head', 'Head', 'Head', None)]
        for side, S_, s in (('Left', 'Left', '_L'), ('Right', 'Right', '_R')):
            spec += [(side + 'Clavicle', S_ + ' shoulder', S_ + ' shoulder', None),
                     (side + 'Arm', S_ + ' arm', S_ + ' wrist', side + 'HandGoal'),
                     (side + 'Thumb', 'Thumb0' + s, 'Thumb2' + s, None),
                     (side + 'Index', 'IndexFinger1' + s, 'IndexFinger3' + s, None),
                     (side + 'Middle', 'MiddleFinger1' + s, 'MiddleFinger3' + s, None),
                     (side + 'Ring', 'RingFinger1' + s, 'RingFinger3' + s, None),
                     (side + 'Pinky', 'LittleFinger1' + s, 'LittleFinger3' + s, None)]
            leg_end_ball = 'ball' in mend(side + 'Leg') or 'toe' in mend(side + 'Leg')
            spec.append((side + 'Leg', S_ + ' leg', S_ + (' toe' if leg_end_ball else ' ankle'), side + 'FootGoal'))
            if not leg_end_ball:
                spec.append((side + 'Foot' if (side + 'foot') in manny_names else side + 'Toe', S_ + ' toe', S_ + ' toe', None))
        # keep the solver for legs/arms: feet planted like the Unity leg fit
        solver = None
        for tn in ('/Script/IKRig.IKRigFullBodyIKSolver', 'IKRigFullBodyIKSolver', 'FBIK'):
            try:
                solver = tc.add_solver(tn); log('solver', tn, solver)
                if solver is not None and solver >= 0: break
            except Exception as e:
                log('add_solver failed', tn, repr(e)); solver = None
        if solver is not None and solver >= 0:
            call(tc, 'set_root_bone', B('Hips'), solver)
        else:
            solver = None
        for name, a, b, goal in spec:
            a, b = B(a), B(b)
            if goal:
                bone = b if 'Hand' in goal else B(b.replace('toe', 'ankle'))
                call(tc, 'add_new_goal', goal, bone)
                if solver is not None: call(tc, 'connect_goal_to_solver', goal, solver)
            call(tc, 'add_retarget_chain', name, a, b, goal or '')
    tchains = []
    for c in tc.get_retarget_chains():
        tchains.append((str(c.get_editor_property('chain_name')), str(c.get_editor_property('start_bone').get_editor_property('bone_name')), str(c.get_editor_property('end_bone').get_editor_property('bone_name'))))
    res['furina_chains'] = tchains
    eal.save_asset(DEST + '/IK_Furina')

    # ---------- retargeter
    rtg, new = get_or_create('RTG_Manny_To_Furina', unreal.IKRetargeter, unreal.IKRetargetFactory())
    rc = unreal.IKRetargeterController.get_controller(rtg)
    res['rtg_ctrl_methods'] = [m for m in dir(rc) if not m.startswith('_')]
    if new:
        S_ = unreal.RetargetSourceOrTarget
        call(rc, 'set_ik_rig', S_.SOURCE, src)
        call(rc, 'set_ik_rig', S_.TARGET, tgt)
        call(rc, 'set_preview_mesh', S_.SOURCE, manny)
        call(rc, 'set_preview_mesh', S_.TARGET, furina)
        if hasattr(rc, 'add_default_ops'): call(rc, 'add_default_ops')
        if hasattr(rc, 'assign_ik_rig_to_all_ops'):
            call(rc, 'assign_ik_rig_to_all_ops', S_.SOURCE, src); call(rc, 'assign_ik_rig_to_all_ops', S_.TARGET, tgt)
        call(rc, 'auto_map_chains', unreal.AutoMapChainType.FUZZY, True)
        # joint alignment: rotate Furina's A-pose bones to match the mannequin rest directions
        try:
            call(rc, 'auto_align_all_bones', S_.TARGET)
        except Exception as e: log('align', repr(e))
    try:
        res['mapping'] = [(str(c.get_editor_property('target_chain')), str(c.get_editor_property('source_chain'))) for c in rc.get_all_chain_settings()] if hasattr(rc, 'get_all_chain_settings') else None
    except Exception as e: res['mapping'] = repr(e)
    eal.save_asset(DEST + '/RTG_Manny_To_Furina')
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('UE_RETARGET_DONE')
