"""Imports Joumae Saori (FBX/Saori/Saori_cm.fbx, built by build_saori_on_furina.py: her meshes skinned to the FURINA skeleton) as /Game/Saori/SK_Saori on /Game/Furina/SK_Furina_Skeleton,
imports her textures to /Game/Saori/Textures and gives every material slot a material instance (parent M_Furina_Opaque = two-sided masked / M_Furina_Translucent) with the matching texture.
-> Data/saori_import.json. usage: py ue_saori_import.py"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SRC = r'C:\Users\fromj\Downloads\joumae-saori\source\Joumae Saori From Blue Archive'
FBX = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\Saori\Saori_cm.fbx'
DEST = '/Game/Saori'
TEXS = {'Body': 'Saori_Original_Body.png', 'Face': 'Saori_Original_Face.png', 'EyeMouth': 'Saori_Original_EyeMouth.png', 'Hair': 'hair2.png', 'HairAtlas': 'Saori_Original_Hair.png', 'Halo': 'Saori_Original_Halo.png', 'Skin': 't000.png'}
# material slot name (from Blender) -> (texture key, translucent)
SLOT = {}
for n in ('Body', 'Body.001', 'Body.002', 'Body.003', 'Body.004', 'Neck', 'Nails1', 'Nails2'): SLOT[n] = ('Skin', False)
for n in ('Mask', 'Pants', 'Belt', 'Shoes', 'Shirt', 'Gloves', 'Hat', 'Coat', 'Pants Accessories'): SLOT[n] = ('Body', False)
for n in ('face', 'eyebrow', 'eyelash', 'eye lid', 'Material', 'eyebrow crease', 'cheek', 'tears', 'Facial Line', 'mouth', 'en', 'en.001', 'eye extra', 'whites', 'teeth', 'eye_hi'): SLOT[n] = ('Face', n in ('cheek', 'tears', 'Facial Line', 'eyebrow crease', 'eye extra', 'en', 'en.001', 'eye_hi'))
SLOT['eye'] = ('EyeMouth', False); SLOT['Hair'] = ('Hair', False); SLOT['Halo'] = ('Halo', True)
for _k in list(SLOT): SLOT[_k.replace(' ', '_').replace('.', '_')] = SLOT[_k]      # UE slot names use underscores (Body.004 -> Body_004)
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    texs = {}
    for k, f in TEXS.items():
        p = DEST + '/Textures/T_Saori_' + k
        if not E.does_asset_exist(p):
            t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f); t.destination_path = DEST + '/Textures'; t.destination_name = 'T_Saori_' + k; t.automated = True; t.save = True; t.replace_existing = True
            T.import_asset_tasks([t])
        a = unreal.load_asset(p); texs[k] = a
    R['textures'] = {k: bool(v) for k, v in texs.items()}
    mp = DEST + '/SK_Saori'
    if not E.does_asset_exist(mp):
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.import_materials = False; ui.import_textures = False; ui.import_animations = False; ui.create_physics_asset = False
        ui.skeleton = unreal.load_asset('/Game/Furina/SK_Furina_Skeleton')
        ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets', False)
        t = unreal.AssetImportTask(); t.filename = FBX; t.destination_path = DEST; t.destination_name = 'SK_Saori'; t.automated = True; t.save = True; t.replace_existing = True; t.options = ui
        T.import_asset_tasks([t]); R['imported'] = [str(x) for x in t.imported_object_paths]
    mesh = unreal.load_asset(mp); assert mesh, 'mesh import failed'
    R['skeleton'] = str(mesh.get_editor_property('skeleton').get_path_name())
    R['bounds'] = str(mesh.get_bounds())
    mats = list(mesh.get_editor_property('materials')); R['slots'] = [str(m.get_editor_property('material_slot_name')) for m in mats]
    opaque = unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque'); trans = unreal.load_asset('/Game/Furina/Materials/M_Furina_Translucent')
    miss = []
    for i, m in enumerate(mats):
        slot = str(m.get_editor_property('material_slot_name')); key, tr = SLOT.get(slot, ('Body', False))
        if slot not in SLOT: miss.append(slot)
        name = 'MI_Saori_' + slot.replace(' ', '_').replace('.', '_'); p = DEST + '/Materials/' + name
        mi = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset(name, DEST + '/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel = unreal.MaterialEditingLibrary
        mel.set_material_instance_parent(mi, trans if tr else opaque); mel.set_material_instance_texture_parameter_value(mi, 'BaseTex', texs[key])
        E.save_loaded_asset(mi, False)
        m.set_editor_property('material_interface', mi); mats[i] = m
    mesh.set_editor_property('materials', mats); E.save_loaded_asset(mesh, False)
    R['unmapped_slots'] = miss; R['ok'] = True
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\saori_import.json', 'w'), indent=1); print('SAORI_IMPORT', R.get('ok'), R.get('error', '')[-500:])
