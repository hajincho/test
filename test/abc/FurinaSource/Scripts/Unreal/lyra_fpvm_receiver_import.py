"""Import the receiver lining into the existing meshes without replacing animations."""
import json
from pathlib import Path

import unreal


def receiver_material():
    folder = '/Game/Furina/FPVM'
    name = 'M_FPVM_ReceiverInterior'
    if unreal.EditorAssetLibrary.does_asset_exist(f'{folder}/{name}'):
        return unreal.load_asset(f'{folder}/{name}')
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property('two_sided', True)
    material.set_editor_property('used_with_skeletal_mesh', True)
    edit = unreal.MaterialEditingLibrary
    base_color = edit.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -320, 0)
    base_color.set_editor_property('constant', unreal.LinearColor(.072, .065, .057, 1))
    assert edit.connect_material_property(base_color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    roughness = edit.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 120)
    roughness.set_editor_property('r', .48)
    assert edit.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)
    metallic = edit.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 240)
    metallic.set_editor_property('r', .63)
    assert edit.connect_material_property(metallic, '', unreal.MaterialProperty.MP_METALLIC)
    edit.recompile_material(material)
    return material


def import_viewmodel(root, name, suffix, material, optic_key=None):
    folder = f'/Game/Furina/FPVM/{name}'
    base_name = f'SK_FPVM_{name}'
    original = unreal.load_asset(f'{folder}/{base_name}')
    skeleton = original.get_editor_property('skeleton')
    mesh_name = f'{base_name}_{suffix}'
    source = root / 'FurinaSource' / 'FBX' / 'FPVM' / (mesh_name + '.fbx')
    assert source.is_file(), source
    editor = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    previous = {str(slot.material_slot_name): slot.material_interface for slot in original.materials}
    before = editor.get_num_verts(original, 0)
    ui = unreal.FbxImportUI()
    ui.set_editor_property('automated_import_should_detect_type', False)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('import_animations', False)
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.set_editor_property('create_physics_asset', False)
    ui.set_editor_property('reset_to_fbx_on_material_conflict', True)   # 2026-11-23: 재질 슬롯이 바뀌면(캐릭터 통일) 예전 슬롯을 번호대로 남기지 말고 FBX 기준으로
    ui.set_editor_property('skeleton', skeleton)
    skeletal_options = ui.get_editor_property('skeletal_mesh_import_data')
    skeletal_options.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = folder
    task.destination_name = mesh_name
    task.automated = True
    task.replace_existing = True
    task.save = False
    task.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(f'{folder}/{mesh_name}')
    assert mesh, task.imported_object_paths
    updated = []
    interior_index = None
    for index, slot in enumerate(mesh.materials):
        name = str(slot.material_slot_name)
        imported = str(slot.get_editor_property('imported_material_slot_name'))
        if 'ReceiverInterior' in (name, imported):
            interior_index = index
            slot.material_interface = material
        elif name in previous:
            slot.material_interface = previous[name]
        elif optic_key:
            source_material = f'/Game/Furina/Weapons/Germany/{optic_key}/MI_DE_{optic_key}_{name}'
            if unreal.EditorAssetLibrary.does_asset_exist(source_material):
                slot.material_interface = unreal.load_asset(source_material)
        updated.append(slot)
    assert interior_index is not None, [str(slot.material_slot_name) for slot in updated]
    mesh.set_editor_property('materials', updated)
    assert mesh.get_editor_property('skeleton') == skeleton, mesh_name
    if optic_key:
        assert any(str(slot.material_slot_name).endswith('_Glass') and slot.material_interface for slot in updated), mesh_name
    after = editor.get_num_verts(mesh, 0)
    assert after > 0
    return mesh, {'parent_vertices': before, 'vertices': after, 'interior_slot': interior_index}


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    root = Path(unreal.Paths.project_dir()).resolve()
    material = receiver_material()
    variants = [('Kar98k', 'Interior', None), ('G43', 'Interior', None), ('Kar98k', 'ZF39', 'kar98k_zf39'),
                ('Kar98k', 'ZF41', 'kar98k_zf41'), ('G43', 'ZF4', 'g43_zf4')]
    results = [import_viewmodel(root, name, suffix, material, optic) for name, suffix, optic in variants]
    for asset in (material, *(mesh for mesh, _ in results)):
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False), asset.get_name()
    report = {mesh.get_name(): data for mesh, data in results}
    (root / 'Saved' / 'FPVMReceiverSaved.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
