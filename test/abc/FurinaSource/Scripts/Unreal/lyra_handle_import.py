"""Lyra 에디터(`py <파일>`, PIE 중지 상태): build_colt_rifle_bolt.py 가 만든 FBX 를 가져온다.
 - FBX/M4/SK_M4A1.fbx(노리쇠 뭉치를 뺀 본체)로 /Game/Furina/M4/SK_M4A1 를 덮어쓴다(같은 스켈레톤, 같은 머티리얼 슬롯 -> 기존 M_Colt_* 재지정)
 - FBX/M4/SM_M4Bolt.fbx 를 /Game/Furina/M4/SM_M4Bolt (정적 메시, 원점 = 소총 원점)로 가져온다
 이전 SK_M4A1 은 먼저 /Game/Furina/Backups/SK_M4A1_pre_handle 로 복제해 둔다.   -> Data/lyra_bolt_import.json"""
import unreal, os, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; DEST = '/Game/Furina/M4'
R = {}
def main():
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    old = unreal.load_asset(DEST + '/SK_M4A1'); R['old_verts'] = old.get_num_vertices(0) if hasattr(old, 'get_num_vertices') else None
    if not E.does_asset_exist('/Game/Furina/Backups/SK_M4A1_pre_handle'):
        R['backup'] = bool(E.duplicate_asset(DEST + '/SK_M4A1', '/Game/Furina/Backups/SK_M4A1_pre_handle'))
    mats = {k: unreal.load_asset(DEST + '/M_Colt_' + n) for k, n in (('colt_m4_main', 'Main'), ('colt_m4_furniture', 'Furniture'), ('matech_rear_sight', 'Rear'), ('stanag_mag', 'Mag'))}
    def imp(path, name, ui):
        task = unreal.AssetImportTask(); task.filename = path; task.destination_path = DEST; task.destination_name = name; task.automated = True; task.save = False; task.replace_existing = True; task.replace_existing_settings = True; task.options = ui
        T.import_asset_tasks([task]); return unreal.load_asset(DEST + '/' + name)
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
    sb = sk.get_bounds(); R['sk_bounds'] = [[round(v, 2) for v in sb.origin.to_tuple()], [round(v, 2) for v in sb.box_extent.to_tuple()]]
    try: R['sk_verts'] = sk.get_num_vertices(0)
    except Exception: pass
    ui2 = unreal.FbxImportUI(); ui2.import_mesh = True; ui2.import_as_skeletal = False; ui2.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH; ui2.import_materials = False; ui2.import_textures = False
    ui2.static_mesh_import_data.set_editor_property('auto_generate_collision', False); ui2.static_mesh_import_data.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    ui2.static_mesh_import_data.set_editor_property('build_nanite', False)
    bo = imp(os.path.join(D, 'FBX', 'M4', 'SM_M4Bolt.fbx'), 'SM_M4Bolt', ui2); assert bo
    assign(lambda: bo.get_editor_property('static_materials'), lambda s: bo.set_editor_property('static_materials', s), 'bolt'); R['bolt_saved'] = E.save_loaded_asset(bo, False)
    ha = imp(os.path.join(D, 'FBX', 'M4', 'SM_M4Handle.fbx'), 'SM_M4Handle', ui2); assert ha
    assign(lambda: ha.get_editor_property('static_materials'), lambda s: ha.set_editor_property('static_materials', s), 'handle'); R['handle_saved'] = E.save_loaded_asset(ha, False)
    hb = ha.get_bounds(); R['handle_bounds'] = [[round(v, 2) for v in hb.origin.to_tuple()], [round(v, 2) for v in hb.box_extent.to_tuple()]]
    b = bo.get_bounds(); R['bolt_bounds'] = [[round(v, 2) for v in b.origin.to_tuple()], [round(v, 2) for v in b.box_extent.to_tuple()]]
try: main()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\Data\lyra_handle_import.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HANDLE_IMPORT', R.get('error', 'ok')[-300:])
