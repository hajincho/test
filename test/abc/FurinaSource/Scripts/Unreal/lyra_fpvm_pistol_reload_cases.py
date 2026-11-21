"""Install visible magazine swaps and cosmetic empty cases."""
import json
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_clip, import_fbx
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, chain, wire
from lyra_fpvm_scope_metals import rendered_metal, source_maps

ROOT = Path(unreal.Paths.project_dir()).resolve()
FOLDER = '/Game/Furina/FX/Pistol'
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BP = unreal.BlueprintEditorLibrary
PISTOLS = {
    'P38': (26.9, 6.9, -1.9),
    'P08': (26.2, 5.9, -.6),
    'PP': (27.5, 7.1, -2.1),
}
CLIPS = ('Idle', 'IdleS', 'IdleA', 'Fire', 'FireS', 'FireA', 'Reload',
         'T_HS', 'T_SH', 'T_HA', 'T_AH', 'T_SA', 'T_AS')


def save(asset):
    assert ASSETS.save_loaded_asset(asset, False), asset.get_name()


def magazine_metal():
    name = 'M_FPVM_Magazine'
    path = f'{FOLDER}/{name}'
    if ASSETS.does_asset_exist(path):
        return unreal.load_asset(path)
    asset = TOOLS.create_asset(name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    asset.set_editor_property('used_with_skeletal_mesh', True)
    edit = unreal.MaterialEditingLibrary
    color = edit.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -380, 0)
    color.set_editor_property('constant', unreal.LinearColor(.063, .074, .084, 1.))
    assert edit.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    for y, value, pin in [(140, .67, unreal.MaterialProperty.MP_METALLIC), (280, .43, unreal.MaterialProperty.MP_ROUGHNESS)]:
        node = edit.create_material_expression(asset, unreal.MaterialExpressionConstant, -380, y)
        node.set_editor_property('r', value)
        assert edit.connect_material_property(node, '', pin)
    edit.recompile_material(asset)
    save(asset)
    return asset


def put_socket(mesh, name, component_ref, point, rotation=None):
    socket = mesh.find_socket(name)
    system = unreal.get_default_object(unreal.SystemLibrary)
    if not socket:
        socket = unreal.SkeletalMeshSocket(outer=mesh)
        system.call_method('SetNamePropertyByName', (socket, 'SocketName', name))
        mesh.add_socket(socket, False)
    system.call_method('SetNamePropertyByName', (socket, 'BoneName', 'VM_Gun'))
    system.call_method('SetVectorPropertyByName', (socket, 'RelativeLocation',
                       unreal.MathLibrary.inverse_transform_location(component_ref, point)))
    if rotation is not None:
        system.call_method('SetRotatorPropertyByName', (socket, 'RelativeRotation',
                           unreal.MathLibrary.inverse_transform_rotation(component_ref, rotation)))


def update_pistol(name, mag):
    folder = f'/Game/Furina/FPVM/{name}'
    mesh_name = f'SK_FPVM_{name}'
    mesh = unreal.load_asset(f'{folder}/{mesh_name}')
    skeleton = mesh.get_editor_property('skeleton')
    previous = {str(slot.material_slot_name): slot.material_interface for slot in mesh.materials}
    import_fbx(mesh_name + '.fbx', folder, mesh_name, mesh=True, skeleton=skeleton, animations=False)
    mesh = unreal.load_asset(f'{folder}/{mesh_name}')
    assert mesh.get_editor_property('skeleton') == skeleton
    slots = mesh.materials
    installed = False
    for slot in slots:
        title = str(slot.material_slot_name)
        material = previous.get(title)
        if title.startswith('MagazineDisplay'):
            material, installed = mag, True
        if material:
            slot.material_interface = material
    assert installed
    mesh.set_editor_property('materials', slots)

    editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = editor.spawn_actor_from_object(mesh, unreal.Vector(), unreal.Rotator())
    try:
        component = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        ref = component.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT)
        assert component.get_bone_index('VM_Mag') >= 0
        put_socket(mesh, 'VM_CaseFX', ref, unreal.Vector(*PISTOLS[name]))
        data = json.loads((ROOT / f'FurinaSource/Data/fpvm_{name.lower()}_stances.json').read_text())['muzzle']
        orientation = unreal.MathLibrary.make_rot_from_yz(unreal.Vector(*data['ue_fwd']), unreal.Vector(*data['ue_up']))
        put_socket(mesh, 'VM_Muzzle', ref, unreal.Vector(*data['ue_cam_cm']), orientation)
    finally:
        editor.destroy_actor(actor)
    mesh.modify()
    save(mesh)
    save(skeleton)
    loaded = [import_clip(folder, skeleton, f'AS_FPVM_{name}_{clip}') for clip in CLIPS]
    for clip in loaded:
        save(clip)
    reload = loaded[CLIPS.index('Reload')]
    library = unreal.AnimationLibrary
    mag_scale = lambda t: library.get_bone_pose_for_time(reload, 'VM_Mag', t, False).scale3d.x
    assert mag_scale(0.) < .01 and mag_scale(.55) > .9 and mag_scale(.8) < .01 and mag_scale(1.09) > .9
    print(f'PISTOL_RELOAD_SAVED {name} {reload.get_play_length():.3f}s')


def import_prop(name, materials, collide):
    path = f'{FOLDER}/{name}'
    if not ASSETS.does_asset_exist(path):
        settings = unreal.FbxImportUI()
        settings.import_materials = False
        settings.import_textures = False
        settings.static_mesh_import_data.auto_generate_collision = False
        settings.static_mesh_import_data.combine_meshes = True
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / f'FurinaSource/FBX/FX/{name}.fbx')
        task.destination_path = FOLDER
        task.destination_name = name
        task.options = settings
        task.automated = True
        TOOLS.import_asset_tasks([task])
    mesh = unreal.load_asset(path)
    assert mesh, path
    for index, slot in enumerate(mesh.static_materials):
        slot_name = str(slot.material_slot_name)
        mesh.set_material(index, materials['Bullet'] if slot_name.startswith('Bullet_') else materials['Case'])
    if collide:
        static = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if not static.get_simple_collision_count(mesh):
            assert static.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX) >= 0
    bounds = mesh.get_bounds().box_extent
    assert .5 < max(bounds.x, bounds.y, bounds.z) < 2., (name, bounds)
    save(mesh)
    return mesh


def ejection_actor(name, mesh):
    target = FOLDER + '/' + name
    if not ASSETS.does_asset_exist(target):
        assert ASSETS.duplicate_asset('/Game/Furina/M4/BP_223Case', target)
    actor = unreal.load_asset(target)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for handle in sub.k2_gather_subobject_data_for_blueprint(actor):
        data = lib.get_data(handle)
        if str(lib.get_variable_name(data)) == 'FXMesh':
            body = lib.get_associated_object(data)
            body.set_static_mesh(mesh)
            body.set_editor_property('override_materials', [])
            body.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
            break
    graph = Graph(actor)
    direction = graph.nodes['TFPCaseDirection'].find_input_pin('Direction')
    direction.break_pin_links()
    assert direction.set_pin_value('43,128,115')
    BP.compile_blueprint(actor)
    assert actor.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    unreal.get_default_object(actor.generated_class()).set_editor_property('initial_life_span', 3.)
    save(actor)
    return actor.generated_class()


def wire_ejection(classes):
    pawn = unreal.load_asset(PAWN)
    graph = Graph(pawn, 'PistolCase_')
    if 'PistolCase_IsPP' in graph.nodes:
        return
    muzzle = graph.nodes['HFX_NSShell'].find_then_pin()
    previous = list(muzzle.list_connected_pins())
    assert previous
    muzzle.break_pin_links()
    def result(name, function, **kwargs):
        return graph.call(name, function, **kwargs).find_result_pin()

    key = graph.get('FurinaVMLastKey')
    who = {p: result(p, STRINGS+'EqualEqual_StrStr', A=key, B=p.lower()) for p in PISTOLS}
    nine = result('NineMM', MATH+'BooleanOR', A=who['P38'], B=who['P08'])
    is_pp = graph.branch('IsPP', who['PP'])
    is_nine = graph.branch('IsNine', nine)
    wire(muzzle, is_pp.find_execute_pin())
    wire(is_pp.find_else_pin(), is_nine.find_execute_pin())
    vm = graph.get('FurinaFPVM')
    position = result('VisibleSocket', ENGINE+'SceneComponent:GetSocketLocation', target=vm, InSocketName='VM_CaseFX')
    rotation = result('ViewDirection', ENGINE+'SceneComponent:K2_GetComponentRotation', target=graph.get('FPCamera'))
    transform = result('CaseTransform', MATH+'MakeTransform', Location=position, Rotation=rotation)
    gs = ENGINE + 'GameplayStatics:'
    outputs = [is_nine.find_else_pin()]
    for label, entry in (('ThirtyTwo', is_pp.find_then_pin()), ('Nine', is_nine.find_then_pin())):
        spawn = graph.call(label+'Spawn', gs+'BeginDeferredActorSpawnFromClass', ActorClass=classes[label],
                           SpawnTransform=transform, CollisionHandlingOverride='AlwaysSpawn')
        finish = graph.call(label+'Finish', gs+'FinishSpawningActor', Actor=spawn.find_result_pin(), SpawnTransform=transform)
        outputs.append(chain(entry, [spawn, finish]))
    for destination in previous:
        for source in outputs:
            wire(source, destination)
    BP.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    save(pawn)


def prepare_cases():
    maps = {key: source_maps(key, FOLDER, 'FurinaSource/Textures/FPVM/PistolMetals')
            for key in ('Metal048B', 'Metal058A', 'NineMM')}
    brass = rendered_metal('32_Case_Metal048B', maps['Metal048B'], (.86, .81, .64), .24, FOLDER)
    copper = rendered_metal('32_Tip_Metal058A', maps['Metal058A'], (.96, .87, .86), .26, FOLDER)
    nine_material = rendered_metal('9mm_Case', maps['NineMM'], (1., .96, .88), .25, FOLDER)
    p32 = import_prop('SM_FPVM_32Case', {'Case': brass}, True)
    p9 = import_prop('SM_FPVM_9mmCase', {'Case': nine_material}, True)
    import_prop('SM_FPVM_32Cartridge', {'Case': brass, 'Bullet': copper}, False)
    return {'ThirtyTwo': ejection_actor('BP_FPVM_32Case', p32), 'Nine': ejection_actor('BP_FPVM_9mmCase', p9)}


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before saving assets'
    world = editor.get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    enabled = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        classes = prepare_cases()
        mag = magazine_metal()
        for name in PISTOLS:
            update_pistol(name, mag)
        for name in ('MP38', 'MP40', 'STG44'):
            folder = f'/Game/Furina/FPVM/{name}'
            skeleton = unreal.load_asset(f'{folder}/SK_FPVM_{name}').get_editor_property('skeleton')
            save(import_clip(folder, skeleton, f'AS_FPVM_{name}_Reload'))
        wire_ejection(classes)
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if enabled else ' 0'))
    print('FPVM_PISTOL_AND_MAGAZINE_SAVED')


if __name__ == '__main__':
    main()
