import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
try:
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(unreal.load_asset('/Game/Furina/ABP_Furina'))
    skel = unreal.load_asset('/Game/Furina/SK_Furina_Skeleton')
    ui = unreal.FbxImportUI()
    ui.import_mesh = True; ui.import_as_skeletal = True
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_materials = False; ui.import_textures = False; ui.import_animations = False
    ui.create_physics_asset = False
    ui.skeleton = skel
    d = ui.skeletal_mesh_import_data
    d.set_editor_property('import_morph_targets', True)
    for k in ('update_skeleton_reference_pose', 'use_t0_as_ref_pose'):
        try: d.set_editor_property(k, k == 'update_skeleton_reference_pose'); res['log'].append('set ' + k)
        except Exception as e: res['log'].append('no ' + k)
    t = unreal.AssetImportTask()
    t.filename = os.path.join(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX', 'Furina_cm.fbx'); t.destination_path = '/Game/Furina'; t.destination_name = 'SK_Furina'
    t.automated = True; t.save = True; t.replace_existing = True; t.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    res['imported'] = list(t.imported_object_paths)
    sk = unreal.load_asset('/Game/Furina/SK_Furina')
    res['skeleton'] = sk.get_editor_property('skeleton').get_path_name()
    res['materials'] = [(str(m.material_slot_name), m.material_interface.get_name() if m.material_interface else None) for m in sk.get_editor_property('materials')]
    for name, getp in (('mesh', sk.get_editor_property('skeleton').get_reference_pose()),):
        for b in ('Hips', 'Left-knee', 'Left-ankle'):
            x = unreal.AnimPoseExtensions.get_bone_pose(getp, b, unreal.AnimPoseSpaces.LOCAL)
            res['%s_%s' % (name, b)] = [str(x.translation), str(x.scale3d)]
        res['hips_world'] = str(unreal.AnimPoseExtensions.get_bone_pose(getp, 'Hips', unreal.AnimPoseSpaces.WORLD).translation)
    res['bounds'] = str(sk.get_bounds())
    res['morphs'] = len(sk.get_all_morph_target_names()) if hasattr(sk, 'get_all_morph_target_names') else None
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_reimport.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('REIMPORT_DONE')
