"""Probe for the first-person work: Manny skeleton bones, Furina bone names, APIs available, character BP components."""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
R = {}
try:
    sk = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Meshes/Manny_Simple_SK')
    skel = sk.get_editor_property('skeleton')
    R['manny_skeleton'] = skel.get_path_name()
    names = [str(sk.get_bone_name(i)) if hasattr(sk, 'get_bone_name') else None for i in range(0)]
    try:
        R['manny_bones'] = [str(n) for n in unreal.SkeletalMeshEditorSubsystem and []]
    except Exception: pass
    # bone names via a temp component-free route
    ref = sk.get_editor_property('skeleton')
    try:
        R['manny_bone_names'] = [str(b) for b in unreal.AnimationLibrary.get_bone_names_for_skeleton(ref)] if hasattr(unreal.AnimationLibrary, 'get_bone_names_for_skeleton') else 'n/a'
    except Exception as e: R['manny_bone_names'] = repr(e)
    R['api'] = {n: hasattr(unreal, n) for n in ('IKRetargetBatchOperation', 'IKRetargeterController', 'AnimMontageFactory', 'FbxImportUI',
                                                 'AnimGraphNode_BlendListByBool', 'AnimGraphNode_ModifyBone', 'AnimGraphNode_Slot')}
    R['bel'] = [n for n in dir(unreal.BlueprintEditorLibrary) if not n.startswith('_')]
    R['retarget_ops'] = [n for n in dir(unreal.IKRetargetBatchOperation) if not n.startswith('_')] if hasattr(unreal, 'IKRetargetBatchOperation') else None
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    comps = []
    for h in handles:
        d = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
        comps.append((str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(d)), o.get_class().get_name() if o else None))
    R['bp_components'] = comps
    cdo = unreal.get_default_object(bp.generated_class())
    R['bp_flags'] = {k: str(cdo.get_editor_property(k)) for k in ('use_controller_rotation_yaw',)}
    R['orient_to_movement'] = cdo.character_movement.get_editor_property('orient_rotation_to_movement')
    fm = [c for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent)]
    R['cdo_meshes'] = [(c.get_name(), str(c.get_editor_property('relative_location')), str(c.get_editor_property('relative_rotation'))) for c in fm]
except Exception:
    R['error'] = traceback.format_exc()
json.dump(R, open(os.path.join(D, 'ue_probe_fp.json'), 'w'), indent=1, default=str)
print('PROBE_FP_DONE')
