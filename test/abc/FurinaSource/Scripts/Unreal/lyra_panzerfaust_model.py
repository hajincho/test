"""Replace the Panzerfaust viewmodel and its in-game props with the supplied asset."""
import json
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import SOURCE, import_clip, import_fbx
from lyra_fpvm_pistol_reload_cases import put_socket
from lyra_launcher_gameplay import ASSETS, MENU, PAWN, PZF, install_menu, install_tab_replacement, make_drop, save

ROOT = Path(unreal.Paths.project_dir()).resolve()
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MODEL = 'SK_FPVM_PANZERFAUST'
SURFACE = 'M_Panzerfaust60'
TEXTURES = PZF + '/Panzerfaust60Textures'
TUBE = 'SM_FPVM_PzfSpentTube'
HEAD = 'SM_FPVM_PzfWarhead'


def import_source(filename, folder, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = str(filename)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    task.options = options
    TOOLS.import_asset_tasks([task])
    assert task.imported_object_paths, filename
    return unreal.load_asset(f'{folder}/{name}')


def material():
    path = PZF + '/' + SURFACE
    if ASSETS.does_asset_exist(path):
        return unreal.load_asset(path)
    tc = unreal.TextureCompressionSettings
    mp = unreal.MaterialProperty
    st = unreal.MaterialSamplerType
    channels = [
        ('BaseColor', tc.TC_DEFAULT, st.SAMPLERTYPE_COLOR, mp.MP_BASE_COLOR, 'RGB'),
        ('Metallic', tc.TC_MASKS, st.SAMPLERTYPE_MASKS, mp.MP_METALLIC, 'R'),
        ('Roughness', tc.TC_MASKS, st.SAMPLERTYPE_MASKS, mp.MP_ROUGHNESS, 'R'),
        ('Normal', tc.TC_NORMALMAP, st.SAMPLERTYPE_NORMAL, mp.MP_NORMAL, 'RGB'),
    ]
    samples = []
    for label, compression, sampler, shader_pin, output in channels:
        name = 'T_Panzerfaust60_' + label
        src = ROOT / 'FurinaSource/Textures/Panzerfaust60' / (name + '.png')
        texture = import_source(src, TEXTURES, name)
        texture.set_editor_property('compression_settings', compression)
        texture.set_editor_property('srgb', label == 'BaseColor')
        save(texture)
        samples.append((texture, sampler, shader_pin, output))

    surface = TOOLS.create_asset(SURFACE, PZF, unreal.Material, unreal.MaterialFactoryNew())
    surface.set_editor_property('two_sided', True)
    surface.set_editor_property('used_with_skeletal_mesh', True)
    edit = unreal.MaterialEditingLibrary
    for index, (texture, sampler, shader_pin, output) in enumerate(samples):
        node = edit.create_material_expression(surface, unreal.MaterialExpressionTextureSample, -450, index * 240)
        node.set_editor_property('texture', texture)
        node.set_editor_property('sampler_type', sampler)
        assert edit.connect_material_property(node, output, shader_pin), shader_pin
    edit.recompile_material(surface)
    save(surface)
    return surface


def apply_viewmodel_material(mesh, surface, original_materials):
    slots = []
    for slot in mesh.materials:
        name = str(slot.material_slot_name)
        if name.startswith('Panzerfaust60Surface'):
            slot.material_interface = surface
        elif name in original_materials:
            slot.material_interface = original_materials[name]
        slots.append(slot)
    mesh.set_editor_property('materials', slots)
    assert any(slot.material_interface == surface for slot in mesh.materials), mesh.get_name()


def setup_viewmodel(surface):
    original = unreal.load_asset(f'{PZF}/{MODEL}')
    skeleton = original.get_editor_property('skeleton')
    original_materials = {str(slot.material_slot_name): slot.material_interface for slot in original.materials}
    import_fbx(MODEL + '.fbx', PZF, MODEL, mesh=True, skeleton=skeleton, animations=False)
    mesh = unreal.load_asset(f'{PZF}/{MODEL}')
    assert mesh.get_editor_property('skeleton') == skeleton
    apply_viewmodel_material(mesh, surface, original_materials)

    socket_file = ROOT / 'FurinaSource/Data/fpvm_launchers_ads.json'
    sockets = json.loads(socket_file.read_text(encoding='utf-8'))['panzerfaust']['sockets']
    editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = editor.spawn_actor_from_object(mesh, unreal.Vector(), unreal.Rotator())
    try:
        component = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        bone = component.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT)
        for name, info in sockets.items():
            point = unreal.Vector(*info['ue_cam_cm'])
            rotation = unreal.MathLibrary.make_rot_from_yz(unreal.Vector(*info['ue_fwd']), unreal.Vector(*info['ue_up']))
            put_socket(mesh, name, bone, point, rotation)
            actual = component.get_socket_transform(name, unreal.RelativeTransformSpace.RTS_COMPONENT)
            assert (actual.translation - point).length() < 0.5, name
    finally:
        editor.destroy_actor(actor)
    save(mesh)
    save(skeleton)
    for animation in ('Idle', 'IdleEmpty', 'Fire', 'Reload'):
        clip = import_clip(PZF, skeleton, f'AS_FPVM_PANZERFAUST_{animation}')
        pose = unreal.AnimationLibrary.get_bone_pose_for_frame(clip, 'VM_Warhead', 0, False)
        assert (pose.scale3d.x < .01) == (animation in ('IdleEmpty', 'Fire', 'Reload')), animation
        save(clip)
    assert any(slot.material_interface == surface for slot in mesh.materials)


def import_prop(name, surface, physical=False):
    ui = unreal.FbxImportUI()
    ui.automated_import_should_detect_type = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_materials = False
    ui.import_textures = False
    ui.static_mesh_import_data.auto_generate_collision = False
    mesh = import_source(SOURCE / (name + '.fbx'), PZF, name, ui)
    for slot in range(len(mesh.static_materials)):
        mesh.set_material(slot, surface)
    if physical:
        collision = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        collision.remove_collisions(mesh)
        assert collision.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX) >= 0
    save(mesh)
    return mesh


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing launcher assets'
    world = editor.get_editor_world()
    command = unreal.SystemLibrary.execute_console_command
    setting = 'Interchange.FeatureFlags.Import.FBX'
    prior = unreal.SystemLibrary.get_console_variable_bool_value(setting)
    command(world, setting + ' 0')
    try:
        surface = material()
        setup_viewmodel(surface)
        head = import_prop(HEAD, surface)
        make_drop(import_prop(TUBE, surface, physical=True))
        projectile = unreal.load_asset('/Game/Furina/FP/BP_FurinaPzfWarhead')
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        lib = unreal.SubobjectDataBlueprintFunctionLibrary
        for handle in sub.k2_gather_subobject_data_for_blueprint(projectile):
            data = lib.get_data(handle)
            if str(lib.get_variable_name(data)) == 'ProjectileVisual':
                component = lib.get_associated_object(data)
                assert component.get_editor_property('static_mesh') == head
                component.set_editor_property('override_materials', [])
                break
        else:
            raise RuntimeError('Missing projectile visual component')
        save(projectile, blueprint=True)
    finally:
        command(world, setting + (' 1' if prior else ' 0'))
    pawn = unreal.load_asset(PAWN)
    install_tab_replacement(pawn)
    save(pawn, blueprint=True)
    menu = unreal.load_asset(MENU)
    install_menu(menu)
    save(menu, blueprint=True)
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True, include_soft_package_references=True)
    print('LEGACY_STATIC_REFERENCES', list(registry.get_referencers(
        '/Game/Furina/Weapons/Germany/panzerfaust/SM_DE_panzerfaust', options)))
    print('PANZERFAUST_MODEL_AND_TAB_SAVED')


if __name__ == '__main__':
    main()

