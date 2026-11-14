"""Imports the free FPS template (rifle + first-person rifle motions on UE5 Manny) and retargets the motions to Furina.
 /Game/Furina/FP/Weapon : SK_AssaultRifle (+ its Fire/Reload anims), T_AssaultRifle_D, MI_AssaultRifle
 /Game/Furina/FP/Manny  : A_FP_AssaultRifle_* on the bundle Mannequin_SKEL (source motions)
 /Game/Furina/FP/Anim   : AS_Furina_FP_* retargeted with RTG_Manny_To_Furina
Rifle model: "Low-Poly AAC Honey Badger" by TastyTony, CC BY 4.0."""
import unreal, os, json, traceback
SRC = r"C:\Users\fromj\Downloads\blender_source_files_freefpstemplate\Blender_Source_Files_FreeFpsTemplate"
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
W, M, A = '/Game/Furina/FP/Weapon', '/Game/Furina/FP/Manny', '/Game/Furina/FP/Anim'
R = {'log': []}
def log(*a): R['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools(); mel = unreal.MaterialEditingLibrary
def run(filename, dest, ui=None, name=None):
    t = unreal.AssetImportTask()
    t.filename = filename; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if name: t.destination_name = name
    if ui: t.options = ui
    tools.import_asset_tasks([t])
    return [str(p) for p in t.imported_object_paths]
def anim_ui(skeleton):
    ui = unreal.FbxImportUI()
    ui.import_mesh = False; ui.import_as_skeletal = True; ui.import_animations = True
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    ui.import_materials = False; ui.import_textures = False
    ui.skeleton = skeleton
    ad = ui.anim_sequence_import_data
    ad.set_editor_property('import_bone_tracks', True)
    ad.set_editor_property('remove_redundant_keys', False)
    ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    return ui
try:
    exp = os.path.join(SRC, '_Exported')
    # ---- rifle mesh, texture, material
    if not eal.does_asset_exist(W + '/T_AssaultRifle_D'):
        run(os.path.join(SRC, 'Textures', 'AssaultRifle', 'T_AssaultRifle_D.png'), W, None, 'T_AssaultRifle_D')
    if not eal.does_asset_exist(W + '/SK_AssaultRifle'):
        ui = unreal.FbxImportUI()
        ui.import_mesh = True; ui.import_as_skeletal = True; ui.import_animations = False
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
        log('rifle', run(os.path.join(exp, 'Meshes', 'SK_AssaultRifle.fbx'), W, ui, 'SK_AssaultRifle'))
    rifle = unreal.load_asset(W + '/SK_AssaultRifle')
    if not eal.does_asset_exist(W + '/MI_AssaultRifle'):
        mi = tools.create_asset('MI_AssaultRifle', W, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque'))
        mel.set_material_instance_texture_parameter_value(mi, 'BaseTex', unreal.load_asset(W + '/T_AssaultRifle_D'))
        eal.save_asset(W + '/MI_AssaultRifle')
    mats = rifle.get_editor_property('materials')
    for sm in mats: sm.set_editor_property('material_interface', unreal.load_asset(W + '/MI_AssaultRifle'))
    rifle.set_editor_property('materials', mats)
    eal.save_asset(W + '/SK_AssaultRifle')
    rskel = rifle.get_editor_property('skeleton')
    R['rifle_bounds'] = str(rifle.get_bounds())
    for f in ('A_FP_WEP_AssaultRifle_Fire', 'A_FP_WEP_AssaultRifle_Reload'):
        if not eal.does_asset_exist(W + '/' + f):
            log(f, run(os.path.join(exp, 'Animations', f + '.fbx'), W, anim_ui(rskel), f))
    # ---- character motions on the bundle Manny skeleton
    manny = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Meshes/Manny_Simple_SK')
    mskel = manny.get_editor_property('skeleton')
    names = [f[:-4] for f in sorted(os.listdir(os.path.join(exp, 'Animations'))) if f.startswith('A_FP_AssaultRifle')]
    for n in names:
        if not eal.does_asset_exist(M + '/' + n):
            log(n, run(os.path.join(exp, 'Animations', n + '.fbx'), M, anim_ui(mskel), n))
    R['manny_anims'] = {n: unreal.load_asset(M + '/' + n).get_play_length() for n in names if eal.does_asset_exist(M + '/' + n)}
    # ---- retarget to Furina
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    furina = unreal.load_asset('/Game/Furina/SK_Furina')
    todo = [eal.find_asset_data(M + '/' + n) for n in names if not eal.does_asset_exist(A + '/' + n.replace('A_FP_AssaultRifle_', 'AS_Furina_FP_'))]
    if todo:
        out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(todo, manny, furina, rtg, search='A_FP_AssaultRifle_', replace='AS_Furina_FP_',
                                                                     target_path=A, use_source_path=False, include_referenced_assets=False, overwrite_existing_files=True)
        for ad in out:
            p = str(ad.package_name)
            dst = A + '/' + p.split('/')[-1]
            if p != dst:
                log('move', p, dst, eal.rename_asset(p, dst))
    for n in names:
        p = A + '/' + n.replace('A_FP_AssaultRifle_', 'AS_Furina_FP_')
        if eal.does_asset_exist(p): eal.save_asset(p)
    R['furina_anims'] = [p for p in eal.list_assets(A, False, False)]
    R['ok'] = True
except Exception:
    R['error'] = traceback.format_exc()
json.dump(R, open(os.path.join(D, 'ue_fp_import.json'), 'w'), indent=1, default=str)
print('FP_IMPORT_DONE')
