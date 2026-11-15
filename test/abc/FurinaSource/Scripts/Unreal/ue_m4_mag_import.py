"""Re-imports SK_M4A1 without the magazine and imports the separated magazine as SM_M4Mag (Scripts/Blender/split_m4_mag.py), 2026-11-15.
Materials: slot names containing AR1..AR4 get /Game/Furina/M4/M_M4_AR1..4 (same as ue_import_m4.py)."""
import unreal, os, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; DEST = '/Game/Furina/M4'
def main():
    R = {}
    e = unreal.EditorAssetLibrary; t = unreal.AssetToolsHelpers.get_asset_tools()
    def imp(path, name, ui):
        task = unreal.AssetImportTask(); task.filename = path; task.destination_path = DEST; task.destination_name = name; task.automated = True; task.save = True; task.replace_existing = True; task.options = ui
        t.import_asset_tasks([task]); return unreal.load_asset(DEST + '/' + name)
    for stray in ('Plane_001_mag', 'Plane_003_mag'):
        if e.does_asset_exist(DEST + '/' + stray): e.delete_asset(DEST + '/' + stray)
    mats = {str(i): unreal.load_asset(DEST + '/M_M4_AR' + str(i)) for i in range(1, 5)}
    def assign(mesh, get_slots, set_slots):
        slots = list(get_slots())
        for slot in slots:
            key = str(slot.get_editor_property('imported_material_slot_name'))
            for i, m in mats.items():
                if 'AR' + i in key: slot.set_editor_property('material_interface', m)
        set_slots(slots); R.setdefault('slots', []).append([str(s.get_editor_property('imported_material_slot_name')) for s in slots])
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_animations = False; ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
    ui.skeleton = unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle_Skeleton')
    sk = imp(os.path.join(D, 'FBX', 'M4', 'SK_M4A1.fbx'), 'SK_M4A1', ui); assert sk
    assign(sk, lambda: sk.get_editor_property('materials'), lambda s: sk.set_editor_property('materials', s)); R['sk_saved'] = e.save_loaded_asset(sk, False)
    ui2 = unreal.FbxImportUI(); ui2.import_mesh = True; ui2.import_as_skeletal = False; ui2.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui2.import_materials = False; ui2.import_textures = False; ui2.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
    mg = imp(os.path.join(D, 'FBX', 'M4', 'SM_M4Mag.fbx'), 'SM_M4Mag', ui2); assert mg
    assign(mg, lambda: mg.get_editor_property('static_materials'), lambda s: mg.set_editor_property('static_materials', s)); R['mag_saved'] = e.save_loaded_asset(mg, False)
    b = mg.get_bounds(); R['mag_bounds'] = [[round(v, 2) for v in b.origin.to_tuple()], [round(v, 2) for v in b.box_extent.to_tuple()]]
    sb = sk.get_bounds(); R['sk_bounds'] = [[round(v, 2) for v in sb.origin.to_tuple()], [round(v, 2) for v in sb.box_extent.to_tuple()]]
    del sk, mg
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'Data', 'm4_mag_import.json'), 'w'), indent=1); print('M4_MAG_IMPORT', R.get('error', 'ok')[:300])
