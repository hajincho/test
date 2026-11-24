"""Import pistol game viewmodels and per-amount reload animations."""
import json
from pathlib import Path

import unreal


ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SOURCE = Path(unreal.Paths.project_dir()).resolve() / 'FurinaSource' / 'FBX' / 'FPVM'


def import_fbx(filename, folder, name, *, mesh, skeleton=None, animations=True):
    options = unreal.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type', False)
    options.set_editor_property('import_mesh', mesh)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH if mesh else unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property('import_animations', animations)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('create_physics_asset', False)
    options.set_editor_property('reset_to_fbx_on_material_conflict', True)   # 2026-11-23: 재질 슬롯이 바뀌면(캐릭터 통일) 예전 슬롯을 번호대로 남기지 말고 FBX 기준으로
    if skeleton:
        options.set_editor_property('skeleton', skeleton)
    settings = options.get_editor_property('anim_sequence_import_data')
    settings.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    settings.set_editor_property('use_default_sample_rate', False)
    settings.set_editor_property('convert_scene_unit', True)
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE / filename)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    task.options = options
    TOOLS.import_asset_tasks([task])
    return [unreal.load_asset(path) for path in task.imported_object_paths]


def rename_animation(animation, folder, name):
    if animation.get_name() == name:
        return animation
    target = f'{folder}/{name}'
    if ASSETS.does_asset_exist(target):
        return unreal.load_asset(target)
    assert ASSETS.rename_asset(animation.get_path_name(), target), target
    return unreal.load_asset(target)


def import_pistol(key):
    name = key.upper()
    folder = '/Game/Furina/FPVM/' + name
    mesh_name = 'SK_FPVM_' + name
    import_fbx(mesh_name + '.fbx', folder, mesh_name, mesh=True, animations=False)
    mesh = unreal.load_asset(folder + '/' + mesh_name)
    skeleton = mesh.get_editor_property('skeleton')
    previous_rifle = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k_Interior')
    defaults = {str(slot.material_slot_name): slot.material_interface for slot in previous_rifle.materials}
    props = unreal.load_asset(f'/Game/Furina/Weapons/Germany/{key}/SM_DE_{key}')
    defaults.update({str(slot.material_slot_name): slot.material_interface for slot in props.static_materials})
    materials = []
    for slot in mesh.materials:
        material = defaults.get(str(slot.material_slot_name))
        if material:
            slot.material_interface = material
        materials.append(slot)
    mesh.set_editor_property('materials', materials)
    loaded = {label: import_clip(folder, skeleton, f'AS_FPVM_{name}_{label}') for label in ('Idle', 'Fire', 'Reload')}
    for asset in (mesh, skeleton, *loaded.values()):
        assert ASSETS.save_loaded_asset(asset, False), asset.get_name()
    return {'mesh': mesh.get_path_name(), **{label: seq.get_play_length() for label, seq in loaded.items()}}


def import_clip(folder, skeleton, name):
    meshless = import_fbx(name + '.fbx', folder, name, mesh=False, skeleton=skeleton)
    animation = next(item for item in meshless if isinstance(item, unreal.AnimSequence))
    match_skeleton_units(animation)
    return rename_animation(animation, folder, name)


def match_skeleton_units(animation):
    # Blender's animation-only FBX can retain a metre-scaled root while the
    # skeletal mesh uses centimetres. Child tracks are already in local units.
    library = unreal.AnimationLibrary
    bone = 'hips'
    sample = library.get_bone_pose_for_frame(animation, bone, 0, False)
    if sample.scale3d.x < 2.:
        poses = [library.get_bone_pose_for_frame(animation, bone, frame, False)
                 for frame in range(library.get_num_keys(animation))]
        assert animation.controller.set_bone_track_keys(
            bone, [p.translation * 100. for p in poses], [p.rotation for p in poses],
            [p.scale3d * 100. for p in poses], False), animation.get_name()
    assert library.get_bone_pose_for_frame(animation, bone, 0, False).scale3d.x > 90., animation.get_name()


def import_reloads():
    results = {}
    for model, suffixes in [('Kar98k', ('Loose1', 'Loose2', 'Loose3', 'Loose4')), ('G43', ('Loose1', 'Loose2', 'Loose3', 'Loose4', 'Clip5', 'Loose6', 'Loose7', 'Loose8', 'Loose9'))]:
        folder = '/Game/Furina/FPVM/' + model
        skeleton = unreal.load_asset(f'{folder}/SK_FPVM_{model}_Skeleton')
        for suffix in suffixes:
            name = f'AS_FPVM_{model}_{suffix}'
            assert (SOURCE / (name + '.fbx')).is_file(), name
            animation = import_clip(folder, skeleton, name)
            assert ASSETS.save_loaded_asset(animation, False)
            results[name] = animation.get_play_length()
    return results


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing assets'
    world = editor.get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    report_path = Path(unreal.Paths.project_dir()).resolve() / 'Saved' / 'FPVMAnimationsSaved.json'
    try:
        pistols = {key: import_pistol(key) for key in ('p38', 'p08', 'pp')}
        report_path.write_text(json.dumps({'pistols': pistols}, indent=2), encoding='utf-8')
        reloads = import_reloads()
        report_path.write_text(json.dumps({'pistols': pistols, 'reloads': reloads}, indent=2), encoding='utf-8')
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))


if __name__ == '__main__':
    main()
