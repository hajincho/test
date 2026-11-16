"""Imports the Colt M4A1 rifle (Scripts/Blender/build_colt_rifle.py) over /Game/Furina/M4/SK_M4A1 and SM_M4Mag and builds the PBR materials, 2026-11-15.
Textures: FBX/M4/ColtTex (2048, made by colt_textures.py) -> /Game/Furina/M4/T_Colt_<mat>_<Map>; materials M_Colt_<Main|Furniture|Rear|Mag> (BaseColor/Metallic/Roughness/Normal/AO).
Slot names containing colt_m4_main / colt_m4_furniture / matech_rear_sight / stanag_mag get the matching material."""
import unreal, os, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; DEST = '/Game/Furina/M4'
def main():
    R = {}
    e = unreal.EditorAssetLibrary; t = unreal.AssetToolsHelpers.get_asset_tools(); ml = unreal.MaterialEditingLibrary
    def imp(path, name, ui):
        task = unreal.AssetImportTask(); task.filename = path; task.destination_path = DEST; task.destination_name = name; task.automated = True; task.save = True; task.replace_existing = True; task.options = ui
        t.import_asset_tasks([task]); return unreal.load_asset(DEST + '/' + name)
    names = {'colt_m4_main': 'Main', 'colt_m4_furniture': 'Furniture', 'matech_rear_sight': 'Rear', 'stanag_mag': 'Mag'}
    mats = {}
    for src, short in names.items():
        name = 'M_Colt_' + short; p = DEST + '/' + name
        mat = unreal.load_asset(p) if e.does_asset_exist(p) else t.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
        ml.delete_all_material_expressions(mat); mat.set_editor_property('used_with_skeletal_mesh', True)
        for suffix, prop, y in (('BaseColor', unreal.MaterialProperty.MP_BASE_COLOR, 0), ('Metallic', unreal.MaterialProperty.MP_METALLIC, 250), ('Roughness', unreal.MaterialProperty.MP_ROUGHNESS, 500), ('Normal', unreal.MaterialProperty.MP_NORMAL, 750), ('AO', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 1000)):
            tn = 'T_Colt_%s_%s' % (short, suffix); ptex = DEST + '/' + tn
            tex = unreal.load_asset(ptex) if e.does_asset_exist(ptex) else imp(os.path.join(D, 'FBX', 'M4', 'ColtTex', '%s_%s.png' % (src, suffix)), tn, None)
            tex.set_editor_property('srgb', suffix == 'BaseColor')
            if suffix == 'Normal': tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
            elif suffix != 'BaseColor': tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS if False else unreal.TextureCompressionSettings.TC_DEFAULT)
            e.save_loaded_asset(tex, False)
            x = ml.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, y); x.set_editor_property('texture', tex)
            x.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix == 'Normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if suffix == 'BaseColor' else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            ml.connect_material_property(x, 'RGB' if suffix in ('BaseColor', 'Normal') else 'R', prop)
        ml.recompile_material(mat); R.setdefault('materials', {})[short] = e.save_loaded_asset(mat, False); mats[src] = mat
    def assign(get_slots, set_slots, tag):
        slots = list(get_slots()); out = []
        for slot in slots:
            key = str(slot.get_editor_property('imported_material_slot_name')); out.append(key)
            for src, m in mats.items():
                if src in key: slot.set_editor_property('material_interface', m)
        set_slots(slots); R.setdefault('slots', {})[tag] = out
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_animations = False; ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
    ui.skeleton = unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle_Skeleton')
    sk = imp(os.path.join(D, 'FBX', 'M4', 'SK_M4A1.fbx'), 'SK_M4A1', ui); assert sk
    assign(lambda: sk.get_editor_property('materials'), lambda s: sk.set_editor_property('materials', s), 'sk'); R['sk_saved'] = e.save_loaded_asset(sk, False)
    ui2 = unreal.FbxImportUI(); ui2.import_mesh = True; ui2.import_as_skeletal = False; ui2.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui2.import_materials = False; ui2.import_textures = False; ui2.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
    mg = imp(os.path.join(D, 'FBX', 'M4', 'SM_M4Mag.fbx'), 'SM_M4Mag', ui2); assert mg
    assign(lambda: mg.get_editor_property('static_materials'), lambda s: mg.set_editor_property('static_materials', s), 'mag'); R['mag_saved'] = e.save_loaded_asset(mg, False)
    b = mg.get_bounds(); R['mag_bounds'] = [[round(v, 2) for v in b.origin.to_tuple()], [round(v, 2) for v in b.box_extent.to_tuple()]]
    sb = sk.get_bounds(); R['sk_bounds'] = [[round(v, 2) for v in sb.origin.to_tuple()], [round(v, 2) for v in sb.box_extent.to_tuple()]]
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'Data', 'colt_import.json'), 'w'), indent=1); print('COLT_IMPORT', R.get('error', 'ok')[:300])
