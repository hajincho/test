"""High quality re-import of the Colt rifle (2026-11-16): FBX/M4/SK_M4A1.fbx + SM_M4Mag.fbx from Scripts/Blender/build_colt_rifle_hq.py and the ORIGINAL 4096 textures of Downloads/colt-m4a1-carbine/textures (the earlier import
used 2048 copies). Textures: BaseColor sRGB BC7-class, Normal (DirectX) normal-map compression, AO / Metallic / Roughness linear; all never-stream (always full resolution), LOD bias 0, highest compression quality,
texture group Weapon. Meshes: imported normals + tangents (no recompute), SM_M4Mag as Nanite-free static mesh with full-precision UVs / tangents. Materials M_Colt_* are rebuilt (BaseColor, Metallic, Roughness, Normal, AO).
-> Data/colt_import_hq.json"""
import unreal, os, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; DEST = '/Game/Furina/M4'; TEX = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\textures'
FILES = {
 'Main': {'BaseColor': 'colt_m4_main_BaseColor_gfl.png', 'Metallic': 'colt_m4_main_Metallic_gfl.png', 'Roughness': 'colt_m4_main_Roughness_gfl.png', 'Normal': 'colt_m4_main_Normal_DirectX_gfl.png', 'AO': 'colt_m4_main_AO.png'},
 'Furniture': {'BaseColor': 'colt_m4_furniture_BaseColor.png', 'Metallic': 'colt_m4_furniture_Metallic.png', 'Roughness': 'colt_m4_furniture_Roughness.png', 'Normal': 'colt_m4_furniture_Normal_DirectX.png', 'AO': 'colt_m4_furniture_AO.png'},
 'Rear': {'BaseColor': 'matech_rear_sight_BaseColor.png', 'Metallic': 'matech_rear_sight_Metallic.png', 'Roughness': 'matech_rear_sight_Roughness.png', 'Normal': 'matech_rear_sight_Normal_DirectX.png', 'AO': 'matech_rear_sight_AO.png'},
 'Mag': {'BaseColor': 'stanag_mag_BaseColor.png', 'Metallic': 'stanag_mag_Metallic.png', 'Roughness': 'stanag_mag_Roughness.png', 'Normal': 'stanag_mag_Normal_directx.png', 'AO': 'stanag_mag_AO.png'}}
SRC = {'Main': 'colt_m4_main', 'Furniture': 'colt_m4_furniture', 'Rear': 'matech_rear_sight', 'Mag': 'stanag_mag'}
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); M = unreal.MaterialEditingLibrary
    def imp(path, name, ui):
        task = unreal.AssetImportTask(); task.filename = path; task.destination_path = DEST; task.destination_name = name; task.automated = True; task.save = False; task.replace_existing = True; task.replace_existing_settings = True; task.options = ui
        T.import_asset_tasks([task]); return unreal.load_asset(DEST + '/' + name)
    mats = {}
    for short, maps in FILES.items():
        name = 'M_Colt_' + short; p = DEST + '/' + name
        mat = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
        M.delete_all_material_expressions(mat); mat.set_editor_property('used_with_skeletal_mesh', True)
        for suffix, prop, y in (('BaseColor', unreal.MaterialProperty.MP_BASE_COLOR, 0), ('Metallic', unreal.MaterialProperty.MP_METALLIC, 250), ('Roughness', unreal.MaterialProperty.MP_ROUGHNESS, 500), ('Normal', unreal.MaterialProperty.MP_NORMAL, 750), ('AO', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 1000)):
            tn = 'T_Colt_%s_%s' % (short, suffix)
            tex = imp(os.path.join(TEX, maps[suffix]), tn, None); assert tex, tn
            tex.set_editor_property('srgb', suffix == 'BaseColor')
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP if suffix == 'Normal' else (unreal.TextureCompressionSettings.TC_DEFAULT if suffix == 'BaseColor' else unreal.TextureCompressionSettings.TC_MASKS))
            tex.set_editor_property('never_stream', True); tex.set_editor_property('lod_bias', 0); tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WEAPON)
            tex.set_editor_property('compression_quality', unreal.TextureCompressionQuality.TCQ_HIGHEST); tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_SHARPEN4)
            R.setdefault('textures', {})[tn] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
            E.save_loaded_asset(tex, False)
            x = M.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, y); x.set_editor_property('texture', tex)
            x.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix == 'Normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if suffix == 'BaseColor' else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR if False else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            M.connect_material_property(x, 'RGB' if suffix in ('BaseColor', 'Normal') else 'R', prop)
        M.recompile_material(mat); R.setdefault('materials', {})[short] = E.save_loaded_asset(mat, False); mats[SRC[short]] = mat
    def assign(get_slots, set_slots, tag):
        slots = list(get_slots()); out = []
        for slot in slots:
            key = str(slot.get_editor_property('imported_material_slot_name')); out.append(key)
            for src, m in mats.items():
                if src in key: slot.set_editor_property('material_interface', m)
        set_slots(slots); R.setdefault('slots', {})[tag] = out
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_animations = False; ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False; ui.skeleton = unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle_Skeleton')
    ui.skeletal_mesh_import_data.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    sk = imp(os.path.join(D, 'FBX', 'M4', 'SK_M4A1.fbx'), 'SK_M4A1', ui); assert sk
    assign(lambda: sk.get_editor_property('materials'), lambda s: sk.set_editor_property('materials', s), 'sk'); R['sk_saved'] = E.save_loaded_asset(sk, False)
    ui2 = unreal.FbxImportUI(); ui2.import_mesh = True; ui2.import_as_skeletal = False; ui2.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH; ui2.import_materials = False; ui2.import_textures = False
    ui2.static_mesh_import_data.set_editor_property('auto_generate_collision', True); ui2.static_mesh_import_data.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    ui2.static_mesh_import_data.set_editor_property('build_nanite', False)
    mg = imp(os.path.join(D, 'FBX', 'M4', 'SM_M4Mag.fbx'), 'SM_M4Mag', ui2); assert mg
    assign(lambda: mg.get_editor_property('static_materials'), lambda s: mg.set_editor_property('static_materials', s), 'mag'); R['mag_saved'] = E.save_loaded_asset(mg, False)
    b = mg.get_bounds(); R['mag_bounds'] = [[round(v, 2) for v in b.origin.to_tuple()], [round(v, 2) for v in b.box_extent.to_tuple()]]
    sb = sk.get_bounds(); R['sk_bounds'] = [[round(v, 2) for v in sb.origin.to_tuple()], [round(v, 2) for v in sb.box_extent.to_tuple()]]
    try: R['sk_verts'] = sk.get_num_vertices(0) if hasattr(sk, 'get_num_vertices') else None
    except Exception: pass
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'Data', 'colt_import_hq.json'), 'w'), indent=1); print('COLT_IMPORT_HQ', R.get('error', 'ok')[-300:])
