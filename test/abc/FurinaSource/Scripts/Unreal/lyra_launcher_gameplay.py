"""Install game-only launcher animation, spent-tube props, and Niagara effects."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import SOURCE, import_clip
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, chain, literal, relay, wire

API = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary
GAME = ENGINE + 'GameplayStatics:'
SYSTEM = ENGINE + 'KismetSystemLibrary:'
NIAGARA = '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation'
FLAME = '/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash.NS_MuzzleFlash'
PZF = '/Game/Furina/FPVM/PANZERFAUST'
DROP = PZF + '/BP_FPVM_PzfSpentTube'
MENU = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
READY = 'FurinaPzfReadyAt'
REQUEST = 'FurinaPzfReplacementRequested'
MENU_REQUEST = 'FurinaPzfMenuRequested'
DISCARDED = 'FurinaPzfDiscarded'
RELEASE_TRANSFORM = 'FurinaPzfReleaseTransform'
COOLDOWN_SECONDS = 30.0
RELEASE_SECONDS = 0.70


def save(asset, *, blueprint=False):
    if blueprint:
        API.compile_blueprint(asset)
        assert asset.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, asset.get_name()
    assert ASSETS.save_loaded_asset(asset, False), asset.get_name()


def import_art(world):
    console = unreal.SystemLibrary.execute_console_command
    setting = 'Interchange.FeatureFlags.Import.FBX'
    was_enabled = unreal.SystemLibrary.get_console_variable_bool_value(setting)
    console(world, setting + ' 0')
    try:
        for name, motion, seconds in [('PANZERFAUST', 'Fire', 1.), ('PANZERSCHRECK', 'Reload', 4.)]:
            folder = '/Game/Furina/FPVM/' + name
            mesh = unreal.load_asset(f'{folder}/SK_FPVM_{name}')
            clip = import_clip(folder, mesh.get_editor_property('skeleton'), f'AS_FPVM_{name}_{motion}')
            assert abs(clip.get_play_length() - seconds) < .04, clip.get_name()
            save(clip)

        name = 'SM_FPVM_PzfSpentTube'
        options = unreal.FbxImportUI()
        for prop, value in {'automated_import_should_detect_type': False, 'import_mesh': True,
                            'import_as_skeletal': False, 'mesh_type_to_import': unreal.FBXImportType.FBXIT_STATIC_MESH,
                            'import_materials': False, 'import_textures': False}.items():
            options.set_editor_property(prop, value)
        task = unreal.AssetImportTask()
        task.filename = str(SOURCE / (name + '.fbx'))
        task.destination_path = PZF
        task.destination_name = name
        task.automated = True
        task.replace_existing = True
        task.options = options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.load_asset(f'{PZF}/{name}')
        size = mesh.get_bounding_box().max - mesh.get_bounding_box().min
        assert 70 < size.x < 110 and size.y < size.x * .5, size
        surface = PZF + '/M_Panzerfaust60'
        if not ASSETS.does_asset_exist(surface):
            surface = '/Game/Furina/Weapons/Germany/panzerfaust/MI_DE_panzerfaust_Material'
        material = unreal.load_asset(surface)
        for index in range(len(mesh.static_materials)):
            mesh.set_material(index, material)
        collision = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        collision.remove_collisions(mesh)
        assert collision.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX) >= 0
        save(mesh)
        return mesh
    finally:
        console(world, setting + (' 1' if was_enabled else ' 0'))


def make_drop(mesh):
    if not ASSETS.does_asset_exist(DROP):
        assert ASSETS.duplicate_asset('/Game/Furina/M4/BP_M4MagDrop', DROP)
    bp = unreal.load_asset(DROP)
    sys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for handle in sys.k2_gather_subobject_data_for_blueprint(bp):
        data = lib.get_data(handle)
        if str(lib.get_variable_name(data)) == 'MagBody':
            body = lib.get_associated_object(data)
            body.set_static_mesh(mesh)
            body.set_simulate_physics(True)
            body.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            body.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
            break
    else:
        raise RuntimeError('The dropped-weapon body template is missing')
    API.compile_blueprint(bp)
    unreal.get_default_object(bp.generated_class()).set_editor_property('initial_life_span', 12.)
    save(bp)


def fields(pawn):
    existing = set(map(str, API.list_member_variable_names(pawn)))
    transform = unreal.EdGraphPinType()
    assert transform.import_text('(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.Transform")')
    field_types = {
        READY: API.get_basic_type_by_name('real'),
        REQUEST: API.get_basic_type_by_name('bool'),
        MENU_REQUEST: API.get_basic_type_by_name('bool'),
        DISCARDED: API.get_basic_type_by_name('bool'),
        RELEASE_TRANSFORM: transform,
    }
    if not set(field_types).issubset(existing):
        for field, field_type in field_types.items():
            if field not in existing:
                assert API.add_member_variable(pawn, field, field_type), field
        API.compile_blueprint(pawn)


def call_result(g, name, function, **inputs):
    return g.call(name, function, **inputs).find_result_pin()


def both(g, name, a, b):
    return call_result(g, name, MATH + 'BooleanAND', A=a, B=b)


def is_pzf(g, name, field):
    return call_result(g, name, STRINGS + 'EqualEqual_StrStr', A=g.get(field), B='panzerfaust')


def add_discard(g, equipped, now):
    vm = g.get('FurinaFPVM')
    front = call_result(g, 'TubeFront', ENGINE + 'SceneComponent:GetSocketLocation', target=vm, InSocketName='VM_Muzzle')
    rear = call_result(g, 'TubeRear', ENGINE + 'SceneComponent:GetSocketLocation', target=vm, InSocketName='VM_Rear')
    midpoint = call_result(g, 'TubeMidpoint', MATH + 'VLerp', A=rear, B=front, Alpha=.5)
    axis = call_result(g, 'TubeAxis', MATH + 'Subtract_VectorVector', A=front, B=rear)
    rot = call_result(g, 'TubeRotation', MATH + 'MakeRotFromX', X=axis)
    world_xf = call_result(g, 'TubeTransform', MATH + 'MakeTransform', Location=midpoint, Rotation=rot)
    stash = g.store('RememberTubeTransform', RELEASE_TRANSFORM, world_xf)
    ready = g.store('StartCooldown', READY, call_result(g, 'CooldownEnds', MATH + 'Add_DoubleDouble', A=now, B=COOLDOWN_SECONDS))
    me = g.nodes['K2Node_FPF_Self'].find_output_pin('self')
    timer = g.call('DropTimer', SYSTEM + 'K2_SetTimer', Object=me, FunctionName='FurinaDropPzfTube',
                   Time=RELEASE_SECONDS, bLooping=False)
    shot = g.nodes['LCH_FinishPzf'].find_then_pin()
    continuation = list(shot.list_connected_pins())
    end = chain_after(shot, [ready, stash, timer])
    for pin in continuation:
        wire(end, pin)

    event = g.editor.add_custom_event_node('FurinaDropPzfTube')
    event.rename(g.prefix + 'DropEvent')
    # Sample the animated tube if still equipped. A quick swap uses the last valid weapon transform.
    use_current = g.branch('StillEquipped', equipped)
    wire(event.find_then_pin(), use_current.find_execute_pin())
    update = g.store('ReleasedTubeTransform', RELEASE_TRANSFORM, world_xf)
    wire(use_current.find_then_pin(), update.find_execute_pin())
    drop = g.store('MarkDiscarded', DISCARDED, True)
    wire(update.find_then_pin(), drop.find_execute_pin())
    wire(use_current.find_else_pin(), drop.find_execute_pin())
    xf = g.get(RELEASE_TRANSFORM)
    spawn = g.call('SpawnTube', GAME + 'BeginDeferredActorSpawnFromClass',
                   ActorClass=unreal.load_asset(DROP).generated_class(), SpawnTransform=xf,
                   CollisionHandlingOverride='AlwaysSpawn')
    finish = g.call('FinishTube', GAME + 'FinishSpawningActor', Actor=spawn.find_result_pin(), SpawnTransform=xf)
    chain(drop.find_then_pin(), [spawn, finish])


def chain_after(source, nodes):
    source.break_pin_links()
    return chain(source, nodes)


def add_replacement(g, equipped, now):
    key_selected = is_pzf(g, 'SelectedPanzerfaust', 'FurinaPrimaryKey')
    start = g.nodes['P2_IA_IA_FurinaWeapon1'].find_output_pin('Started')
    want = g.branch('PrimaryKeyRequestsPanzerfaust', key_selected)
    set_request = g.store('RequestReplacement', REQUEST, True)
    wire(start, want.find_execute_pin())
    wire(want.find_then_pin(), set_request.find_execute_pin())

    # Process replacement after weapon selection has applied the new viewmodel and ammo.
    hide = g.nodes['ScopeView_HideViewmodel']
    hide_input = hide.find_input_pin('NewHidden')
    old_visibility = list(hide_input.list_connected_pins())
    empty = both(g, 'EmptyPanzerfaust', equipped, g.get(DISCARDED))
    hide_input.break_pin_links()
    if old_visibility:
        empty = call_result(g, 'HideSpentOrPrevious', MATH + 'BooleanOR', A=empty, B=old_visibility[0])
    wire(empty, hide_input)

    waiting = g.branch('CheckRequest', both(g, 'ReplacementPending', g.get(REQUEST), key_selected))
    applied = g.branch('CheckEquipped', equipped)
    available = g.branch('CheckCooldown', both(g, 'CanReplace', g.get(DISCARDED),
                         call_result(g, 'IsReady', MATH + 'GreaterEqual_DoubleDouble', A=now, B=g.get(READY))))
    input_ = hide.find_execute_pin()
    previous = list(input_.list_connected_pins())
    input_.break_pin_links()
    for pin in previous:
        wire(pin, waiting.find_execute_pin())
    wire(waiting.find_then_pin(), applied.find_execute_pin())
    clear = g.store('ConsumeRequest', REQUEST, False)
    chain(applied.find_then_pin(), [clear, available])
    for src in (waiting.find_else_pin(), applied.find_else_pin(), available.find_else_pin()):
        wire(src, input_)

    restore = [
        g.store('ReceiveNewTube', DISCARDED, False),
        g.store('ResetCooldown', READY, 0.),
        g.store('Refill', 'FurinaAmmo', 1),
        g.store('RestoreLoadedIdle', 'FurinaVMAnimIdle', unreal.load_asset(PZF + '/AS_FPVM_PANZERFAUST_Idle')),
        g.store('PlayLoadedIdle', 'FurinaVMIdle', False),
    ]
    wire(chain(available.find_then_pin(), restore), input_)
    # Prevent the ordinary reload key from replenishing an expendable launcher.
    g.nodes['LCH_RlBranch_PANZERFAUST'].find_then_pin().break_pin_links()


def install_tab_replacement(pawn):
    g = Graph(pawn, 'LauncherGameplay_')
    if 'LauncherGameplay_MenuOrSlot' in g.nodes:
        return
    fields(pawn)
    g = Graph(pawn, 'LauncherGameplay_')
    menu_requested = g.get(MENU_REQUEST)
    pending = g.nodes['LauncherGameplay_ReplacementPending'].find_input_pin('A')
    previous = pending.list_connected_pins()[0]
    pending.break_pin_links()
    wire(call_result(g, 'BothRequestSources', MATH + 'BooleanOR', A=previous, B=menu_requested), pending)

    clear = g.nodes['LauncherGameplay_ConsumeRequest']
    cooldown = g.nodes['LauncherGameplay_CheckCooldown']
    menu = g.branch('MenuOrSlot', menu_requested)
    relay(clear.find_then_pin(), menu.find_execute_pin(), menu.find_else_pin())
    assert cooldown.find_execute_pin() in menu.find_else_pin().list_connected_pins()
    clear_menu = g.store('ConsumeMenuRequest', MENU_REQUEST, False)
    has_spent_tube = call_result(g, 'SpentTubeExists', MATH + 'Greater_DoubleDouble', A=g.get(READY), B=0.)
    needs_supply = g.branch('MenuNeedsTube', has_spent_tube)
    chain(menu.find_then_pin(), [clear_menu, needs_supply])
    hide = g.nodes['ScopeView_HideViewmodel'].find_execute_pin()
    wire(needs_supply.find_else_pin(), hide)

    # An early menu pick releases the previous tube once and cancels its pending callback.
    already_dropped = g.branch('AlreadyDropped', g.get(DISCARDED))
    wire(needs_supply.find_then_pin(), already_dropped.find_execute_pin())
    restore = g.nodes['LauncherGameplay_ReceiveNewTube']
    wire(already_dropped.find_then_pin(), restore.find_execute_pin())
    me = g.nodes['K2Node_FPF_Self'].find_output_pin('self')
    cancel = g.call('CancelDropTimer', SYSTEM + 'K2_ClearTimer', Object=me, FunctionName='FurinaDropPzfTube')
    drop = g.call('ReleaseTubeNow', pawn.generated_class().get_path_name() + ':FurinaDropPzfTube')
    wire(chain(already_dropped.find_else_pin(), [cancel, drop]), restore.find_execute_pin())

    ready_to_fire = g.store('ClearOldFireAnimation', 'FurinaVMBusy', 0.)
    relay(g.nodes['LauncherGameplay_PlayLoadedIdle'].find_then_pin(), ready_to_fire.find_execute_pin(),
          ready_to_fire.find_then_pin())


def install_pawn(pawn):
    g = Graph(pawn, 'LauncherGameplay_')
    if 'LauncherGameplay_DropEvent' not in g.nodes:
        fields(pawn)
        g = Graph(pawn, 'LauncherGameplay_')
        weapon_is_pzf = is_pzf(g, 'EquippedPanzerfaust', 'FurinaGameWeaponId')
        pistol_active = call_result(g, 'SidearmActive', ENGINE + 'ActorComponent:IsActive', target=g.get('FurinaPistolOn'))
        primary_active = call_result(g, 'PrimaryActive', MATH + 'Not_PreBool', A=pistol_active)
        equipped = both(g, 'HoldingPanzerfaust', weapon_is_pzf, primary_active)
        now = call_result(g, 'Now', GAME + 'GetTimeSeconds')
        add_discard(g, equipped, now)
        add_replacement(g, equipped, now)

        scale = g.nodes['LCH_RearXf'].find_input_pin('Scale')
        prior = scale.list_connected_pins()[0]
        scale.break_pin_links()
        flash = call_result(g, 'LargerFlash', MATH + 'Multiply_VectorFloat', A=prior, B=1.35)
        wire(flash, scale)
    rear = g.nodes['LCH_RearNS']
    literal(rear, 'Scale', '0.50,0.72,0.48')
    if 'LauncherGameplay_RearFlame' not in g.nodes:
        loc = rear.find_input_pin('Location').list_connected_pins()[0]
        rot = rear.find_input_pin('Rotation').list_connected_pins()[0]
        flame = g.call('RearFlame', NIAGARA, SystemTemplate=FLAME, Location=loc, Rotation=rot, bAutoActivate=False)
        component = flame.find_result_pin()
        ns = '/Script/Niagara.NiagaraComponent:'
        size = g.call('FlameSize', ns + 'SetVariableFloat', target=component, InVariableName='Global Scale', InValue=2.3)
        shell = g.call('FlameNoShell', ns + 'SetVariableBool', target=component, InVariableName='Use Bullet Shell', InValue=False)
        play = g.call('PlayFlame', ENGINE + 'ActorComponent:Activate', target=component, bReset=True)
        relay(rear.find_then_pin(), flame.find_execute_pin(), play.find_then_pin())
        chain(flame.find_then_pin(), [size, shell, play])


def install_menu(wbp):
    g = Graph(wbp, 'LauncherGameplay_')
    g.editor = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnPreviewMouseButtonDown')
    nodes = {n.get_name(): n for n in g.editor.list_all_nodes()}
    if 'LauncherGameplay_MenuReplacement' in nodes:
        literal(nodes['LauncherGameplay_MenuReplacement'], 'PropertyName', MENU_REQUEST)
        return
    choose = next(n for n in nodes.values()
                  if n.get_name().startswith('WS_K_') and str(n.find_input_pin('Value').get_pin_value()) == 'panzerfaust')
    owner = choose.find_input_pin('Object').list_connected_pins()[0]
    request = g.call('MenuReplacement', SYSTEM + 'SetBoolPropertyByName', Object=owner,
                     PropertyName=MENU_REQUEST, Value=True)
    relay(choose.find_then_pin(), request.find_execute_pin(), request.find_then_pin())


def install_impact(blueprint):
    g = Graph(blueprint, 'LauncherGameplay_')
    boom = g.nodes['LCH_Boom']
    literal(boom, 'Scale', '1.55,1.55,1.55')
    if 'LauncherGameplay_RisingBlast' not in g.nodes:
        location = boom.find_input_pin('Location').list_connected_pins()[0]
        lifted = call_result(g, 'RisingBlastLocation', MATH + 'Add_VectorVector', A=location, B='0,0,55')
        cloud = g.call('RisingBlast', NIAGARA, SystemTemplate=str(boom.find_input_pin('SystemTemplate').get_pin_value()),
                       Location=lifted, Scale='0.74,0.74,1.12')
        relay(boom.find_then_pin(), cloud.find_execute_pin(), cloud.find_then_pin())


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing launcher assets'
    make_drop(import_art(editor.get_editor_world()))
    pawn = unreal.load_asset(PAWN)
    install_pawn(pawn)
    install_tab_replacement(pawn)
    save(pawn, blueprint=True)
    menu = unreal.load_asset(MENU)
    install_menu(menu)
    save(menu, blueprint=True)
    for name in ('BP_FurinaPzfWarhead', 'BP_FurinaPzsRocket'):
        item = unreal.load_asset('/Game/Furina/FP/' + name)
        install_impact(item)
        save(item, blueprint=True)
    print('LAUNCHER_GAMEPLAY_SAVED')


if __name__ == '__main__':
    main()

