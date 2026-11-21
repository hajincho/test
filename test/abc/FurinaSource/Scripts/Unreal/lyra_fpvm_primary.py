"""Connect primary pistol props and amount-specific rifle reloads to the game."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, HUD, MATH, PAWN, STRINGS, Graph, chain, literal, view_transform, wire


ASSETS = unreal.EditorAssetLibrary
MAP = ENGINE + 'BlueprintMapLibrary:'
SYSTEM = ENGINE + 'KismetSystemLibrary:'
CLIP_SIZES = {'kar98k': 5, 'g43': 10, 'legacy': 20, 'p38': 8, 'p08': 8, 'pp': 8}


def value(node):
    return node.find_result_pin()


def and_(g, name, a, b):
    return value(g.call(name, MATH + 'BooleanAND', A=a, B=b))


def constant(g, name, number):
    return value(g.call(name, SYSTEM + 'MakeLiteralInt', Value=number))


def configure_fields(pawn):
    api = unreal.BlueprintEditorLibrary
    ammo_map = unreal.EdGraphPinType()
    assert ammo_map.import_text('(PinCategory="string",PinValueType=(TerminalCategory="int"),ContainerType=Map)')
    fields = {
        'FurinaGameWeaponId': api.get_basic_type_by_name('string'),
        'FurinaGameCapacity': api.get_basic_type_by_name('int'),
        'FurinaSavedWeaponAmmo': ammo_map,
        'FurinaLooseReload': api.get_basic_type_by_name('bool'),
    }
    existing = {str(name) for name in api.list_member_variable_names(pawn)}
    for name, field in fields.items():
        if name not in existing:
            assert api.add_member_variable(pawn, name, field), name


def weapon_ammo(g, source, key, target):
    previous = g.get('FurinaGameWeaponId')
    ammo = g.get('FurinaAmmo')
    ammo_map = g.get('FurinaSavedWeaponAmmo')
    store = g.call('SaveRounds_' + key + '_' + str(len(g.editor.list_all_nodes())), MAP + 'Map_Add', TargetMap=ammo_map, Key=previous, Value=ammo)
    current = g.store('Group_' + str(len(g.editor.list_all_nodes())), 'FurinaGameWeaponId', key)
    capacity = g.store('Capacity_' + str(len(g.editor.list_all_nodes())), 'FurinaGameCapacity', CLIP_SIZES[key])
    read = g.call('FindRounds_' + str(len(g.editor.list_all_nodes())), MAP + 'Map_Find', TargetMap=ammo_map, Key=current.find_output_pin('Output_Get'))
    choose = g.call('ChooseRounds_' + str(len(g.editor.list_all_nodes())), MATH + 'SelectInt',
                    A=read.find_output_pin('Value'), bPickA=read.find_output_pin('ReturnValue'))
    wire(capacity.find_output_pin('Output_Get'), choose.find_input_pin('B'))
    loaded = g.store('SetRounds_' + str(len(g.editor.list_all_nodes())), 'FurinaAmmo', value(choose))
    source.break_pin_links()
    wire(chain(source, [store, current, capacity, loaded]), target)


def install_selection(pawn):
    g = Graph(pawn, 'HistoryPrimary_')
    if 'HistoryPrimary_Equip_P38' in g.nodes:
        return
    vm = g.get('FurinaFPVM')
    weapon_key = g.get('FurinaPrimaryKey')
    reload_idle = value(g.call('CanChange', MATH + 'Not_PreBool', A=g.get('FurinaReloading')))
    key_changed = g.locate('VW_KeyNe_')
    condition = g.locate('VW_Br_4_').find_input_pin('Condition')
    condition.break_pin_links()
    wire(and_(g, 'ChangeWhenReady', value(key_changed), reload_idle), condition)
    swap = g.locate('VW_S_7_').find_then_pin()
    previous = list(swap.list_connected_pins())
    swap.break_pin_links()
    next_condition = swap
    update = g.locate('VM_Br_12_').find_execute_pin()
    for key in ('p38', 'p08', 'pp'):
        name = key.upper()
        folder = f'/Game/Furina/FPVM/{name}'
        is_key = value(g.call('Key_' + name, STRINGS + 'EqualEqual_StrStr', A=weapon_key, B=key))
        branch = g.branch('Is_' + name, is_key)
        wire(next_condition, branch.find_execute_pin())
        next_condition = branch.find_else_pin()
        mesh = unreal.load_asset(f'{folder}/SK_FPVM_{name}')
        equip = g.call('Equip_' + name, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=vm, NewMesh=mesh)
        actions = [equip]
        # Any old material overrides follow the component, so clear them at swap.
        for index in range(10):
            actions.append(g.call(f'ResetMaterial_{name}_{index}', ENGINE + 'PrimitiveComponent:SetMaterial', target=vm, ElementIndex=index))
        for label in ('Idle', 'Fire', 'Reload'):
            asset = unreal.load_asset(f'{folder}/AS_FPVM_{name}_{label}')
            actions.append(g.store(f'{label}_{name}', 'FurinaVMAnim' + label, asset))
        loc, rot = view_transform(key)
        actions.extend([
            g.store('ADSLocation_' + name, 'FurinaVMAdsLoc', loc),
            g.store('ADSRotation_' + name, 'FurinaVMAdsRot', rot),
            g.store('FireTime_' + name, 'FurinaVMFireLen', .30),
            g.store('ReloadTime_' + name, 'FurinaVMReloadLen', 1.8),
            g.store('NoScope_' + name, 'FurinaScopeZoom', 1.),
            g.store('Valid_' + name, 'FurinaVMValid', True),
        ])
        weapon_ammo(g, chain(branch.find_then_pin(), actions), key, update)
    for target in previous:
        wire(next_condition, target)
    capacity_nodes = [('VW_S_24_', 'kar98k'), ('VW_S_41_', 'g43'), ('VW_S_42_', 'legacy')]
    for node, key in capacity_nodes:
        weapon_ammo(g, g.locate(node).find_then_pin(), key, update)

    # The 1-slot weapons all use a single shot per input press.
    history = value(g.call('EquippedPrimary', STRINGS + 'NotEqual_StrStr', A=g.get('FurinaGameWeaponId'), B='legacy'))
    prior_semi = g.nodes['FM_NotSemi'].find_input_pin('A').list_connected_pins()[0]
    semi = value(g.call('SingleShot', MATH + 'BooleanOR', A=history, B=prior_semi))
    for name, pin in [('FM_NotSemi', 'A'), ('FM_Delay', 'bPickA')]:
        destination = g.nodes[name].find_input_pin(pin)
        destination.break_pin_links()
        wire(semi, destination)

    # Start the first-person firing motion only when the shot can consume a round.
    for node in g.nodes.values():
        if not node.get_name().startswith('VM_Ready_'):
            continue
        signal = node.find_result_pin()
        targets = list(signal.list_connected_pins())
        signal.break_pin_links()
        loaded = g.call('Loaded', MATH + 'Greater_IntInt', A=g.get('FurinaAmmo'), B=constant(g, 'Empty', 0))
        ready = and_(g, 'CanAnimateShot', and_(g, 'HasLoadedRound', value(loaded), reload_idle), signal)
        for pin in targets:
            wire(ready, pin)
        break


def bind_scope_ammo(pawn):
    graph = Graph(pawn)
    for scope, rifle in (('ZF39', 'VW_S_24_'), ('ZF41', 'VW_S_24_'), ('ZF4', 'VW_S_41_')):
        end = graph.nodes['ScopeView_Valid_' + scope].find_then_pin()
        destination, = graph.locate(rifle).find_then_pin().list_connected_pins()
        end.break_pin_links()
        wire(end, destination)


def create_round_props(pawn):
    path = '/Game/Furina/FPVM/SM_FPVM_LooseRound'
    if not ASSETS.does_asset_exist(path):
        ui = unreal.FbxImportUI()
        ui.import_as_skeletal = False
        ui.import_materials = False
        ui.import_textures = False
        task = unreal.AssetImportTask()
        task.filename = str(Path(unreal.Paths.project_dir()).resolve() / 'FurinaSource/FBX/FPVM/SM_FPVM_LooseRound.fbx')
        task.destination_path = '/Game/Furina/FPVM'
        task.destination_name = 'SM_FPVM_LooseRound'
        task.automated = True
        task.options = ui
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    round_mesh = unreal.load_asset(path)
    assert round_mesh
    for i, slot in enumerate(round_mesh.static_materials):
        slot_name = str(slot.material_slot_name)
        original = 'case' if 'Case' in slot_name else '6_5'
        round_mesh.set_material(i, unreal.load_asset('/Game/Furina/Weapons/Germany/mauser_clip/MI_DE_mauser_clip_' + original))
    assert ASSETS.save_loaded_asset(round_mesh, False)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(pawn)}
    if 'FurinaLooseRound' not in handles:
        handle, error = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles['FurinaFPVM'], new_class=unreal.StaticMeshComponent, blueprint_context=pawn))
        assert not str(error), str(error)
        sub.rename_subobject(handle, unreal.Text('FurinaLooseRound'))
    else:
        handle = handles['FurinaLooseRound']
    component = lib.get_associated_object(lib.get_data(handle))
    component.set_static_mesh(round_mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property('cast_shadow', False)
    component.set_editor_property('only_owner_see', True)
    component.set_editor_property('hidden_in_game', True)
    component.set_editor_property('visible', True)

    name = 'M_FPVM_HiddenClip'
    if ASSETS.does_asset_exist(f'/Game/Furina/FPVM/{name}'):
        return unreal.load_asset(f'/Game/Furina/FPVM/{name}')
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Furina/FPVM', unreal.Material, unreal.MaterialFactoryNew())
    asset.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    asset.set_editor_property('used_with_skeletal_mesh', True)
    edit = unreal.MaterialEditingLibrary
    mask = edit.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 0)
    mask.set_editor_property('r', 0.)
    assert edit.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    edit.recompile_material(asset)
    assert ASSETS.save_loaded_asset(asset, False)
    return asset


def install_reload(pawn, mask):
    g = Graph(pawn, 'HistoryReload_')
    if 'HistoryReload_HasWeapon' in g.nodes:
        return
    vm = g.get('FurinaFPVM')
    loose_prop = g.get('FurinaLooseRound')
    weapon_id = g.get('FurinaGameWeaponId')
    legacy = g.nodes['M4_ReloadGate'].find_execute_pin()
    old = list(legacy.list_connected_pins())
    equipped = value(g.call('Historic', STRINGS + 'NotEqual_StrStr', A=weapon_id, B='legacy'))
    sidearm = value(g.call('Sidearm', ENGINE + 'ActorComponent:IsActive', target=g.get('FurinaPistolOn')))
    primary = value(g.call('IsPrimary', MATH + 'Not_PreBool', A=sidearm))
    source = g.branch('HasWeapon', and_(g, 'HistoricPrimary', equipped, primary))
    legacy.break_pin_links()
    for origin in old:
        wire(origin, source.find_execute_pin())
    wire(source.find_else_pin(), legacy)

    room = g.call('Room', MATH + 'Subtract_IntInt', A=g.get('FurinaGameCapacity'), B=g.get('FurinaAmmo'))
    transfer = g.call('Transfer', MATH + 'Min', A=value(room), B=g.get('FurinaReserve'))
    eligible = g.call('HasRounds', MATH + 'Greater_IntInt', A=value(transfer), B=constant(g, 'Zero', 0))
    not_reloading = g.call('NotReloading', MATH + 'Not_PreBool', A=g.get('FurinaReloading'))
    now = g.call('Now', ENGINE + 'GameplayStatics:GetTimeSeconds')
    ready = g.call('IsReady', MATH + 'GreaterEqual_DoubleDouble', A=value(now), B=g.get('FurinaVMBusy'))
    can_start = and_(g, 'Eligible', and_(g, 'NotBusy', value(not_reloading), value(ready)), value(eligible))
    start = g.branch('CanReload', can_start)
    wire(source.find_then_pin(), start.find_execute_pin())
    amount = g.store('Amount', 'FurinaReloadAmount', value(transfer))
    wire(start.find_then_pin(), amount.find_execute_pin())

    me = next(node for node in g.nodes.values() if node.get_class().get_name() == 'K2Node_Self').find_output_pin('self')
    timer = g.call('FinishTimer', SYSTEM + 'K2_SetTimer', Object=me, FunctionName='FurinaFinishReload', Time=g.get('FurinaVMReloadLen'), bLooping=False)
    launch = g.store('SetReloading', 'FurinaReloading', True)
    wire(launch.find_then_pin(), timer.find_execute_pin())

    prepare = g.branch('PrepareProp', g.get('FurinaLooseReload'))
    attached = g.call('AttachRound', ENGINE + 'SceneComponent:K2_AttachToComponent', target=loose_prop, Parent=vm, SocketName='VM_Clip',
                      LocationRule='SnapToTarget', RotationRule='SnapToTarget', ScaleRule='SnapToTarget', bWeldSimulatedBodies=False)
    locate_clip = g.call('LocateClipMaterial', ENGINE + 'PrimitiveComponent:GetMaterialIndex', target=vm, MaterialSlotName='Clip_Steel')
    hide_clip = g.call('HideClip', ENGINE + 'PrimitiveComponent:SetMaterial', target=vm, ElementIndex=value(locate_clip), Material=mask)
    show_round = g.call('RevealRound', ENGINE + 'SceneComponent:SetHiddenInGame', target=loose_prop, NewHidden=False)
    sequence = [attached]
    if locate_clip.find_execute_pin().is_valid():
        sequence.append(locate_clip)
    wire(chain(prepare.find_then_pin(), [*sequence, hide_clip, show_round]), launch.find_execute_pin())
    wire(prepare.find_else_pin(), launch.find_execute_pin())

    selected_amount = amount.find_output_pin('Output_Get')
    entry = amount.find_then_pin()
    for key, family, max_amount in [('kar98k', 'Kar98k', 5), ('g43', 'G43', 10), ('p38', 'P38', 8), ('p08', 'P08', 8), ('pp', 'PP', 8)]:
        match = g.call('Group_' + key, STRINGS + 'EqualEqual_StrStr', A=weapon_id, B=key)
        select = g.branch('Choose_' + key, value(match))
        wire(entry, select.find_execute_pin())
        entry = select.find_else_pin()
        tail = select.find_then_pin()
        cases = range(1, max_amount + 1) if key in ('kar98k', 'g43') else (0,)
        for count in cases:
            loose = count not in (0, 5, 10)
            suffix = f'Loose{count}' if loose else 'Clip5' if key == 'g43' and count == 5 else 'Reload'
            asset = unreal.load_asset(f'/Game/Furina/FPVM/{family}/AS_FPVM_{family}_{suffix}')
            assert asset, (family, suffix)
            if count > 0:
                case = g.call(f'Match_{key}_{count}', MATH + 'EqualEqual_IntInt', A=selected_amount, B=constant(g, f'N_{key}_{count}', count))
                branch = g.branch(f'Amount_{key}_{count}', value(case))
                wire(tail, branch.find_execute_pin())
                origin, tail = branch.find_then_pin(), branch.find_else_pin()
            else:
                origin = tail
            plan = [g.store(f'Clip_{key}_{count}', 'FurinaVMAnimReload', asset),
                    g.store(f'Duration_{key}_{count}', 'FurinaVMReloadLen', asset.get_play_length()),
                    g.store(f'Loose_{key}_{count}', 'FurinaLooseReload', loose)]
            wire(chain(origin, plan), prepare.find_execute_pin())

    finish = g.nodes['M4_ReloadDone']
    clean = g.branch('RestoreClip', g.get('FurinaLooseReload'))
    cutoff = g.call('HideRound', ENGINE + 'SceneComponent:SetHiddenInGame', target=loose_prop, NewHidden=True)
    reset_slot = g.call('FindClipAgain', ENGINE + 'PrimitiveComponent:GetMaterialIndex', target=vm, MaterialSlotName='Clip_Steel')
    restore = g.call('RestoreClipMaterial', ENGINE + 'PrimitiveComponent:SetMaterial', target=vm, ElementIndex=value(reset_slot))
    clear = g.store('ClearLoose', 'FurinaLooseReload', False)
    wire(finish.find_then_pin(), clean.find_execute_pin())
    sequence = [cutoff]
    if reset_slot.find_execute_pin().is_valid():
        sequence.append(reset_slot)
    chain(clean.find_then_pin(), [*sequence, restore, clear])


def fit_loose_prop(pawn):
    graph = Graph(pawn, 'HistoryReload_')
    if 'HistoryReload_PropScale' in graph.nodes:
        return
    attached = graph.nodes['HistoryReload_AttachRound'].find_then_pin()
    continuation, = attached.list_connected_pins()
    scale = graph.call('PropScale', ENGINE + 'SceneComponent:SetRelativeScale3D',
                       target=graph.get('FurinaLooseRound'), NewScale3D='0.01,0.01,0.01')
    attached.break_pin_links()
    wire(attached, scale.find_execute_pin())
    wire(scale.find_then_pin(), continuation)


def hide_weapon_hud():
    hud = unreal.load_asset(HUD)
    graph = Graph(hud)
    condition = graph.nodes['HistoricalView_DrawOnlyLegacy'].find_input_pin('Condition')
    condition.break_pin_links()
    assert condition.set_pin_value('true')
    unreal.BlueprintEditorLibrary.compile_blueprint(hud)
    assert hud.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(hud, False)


def update_menu_tooltips():
    path = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
    menu = unreal.load_asset(path)
    tree = unreal.find_object(None, path + '.WBP_FurinaWeaponMenu:WidgetTree')
    buttons = {
        'Btn_0_0_0': 'Walther P38', 'Btn_0_0_1': 'Luger P08', 'Btn_0_0_2': 'Walther PP',
        'Btn_0_1_0': 'Kar98k', 'Btn_0_1_1': 'Gewehr 43',
        'Btn_0_5_0': 'Kar98k · ZF39 (4×)', 'Btn_0_5_1': 'Kar98k · ZF41 (1.5×)',
        'Btn_0_5_2': 'Gewehr 43 · ZF4 (4×)', 'Btn_0_6_0': 'Walther P38', 'Btn_0_6_1': 'Luger P08',
    }
    for widget in unreal.ObjectIterator(unreal.Button):
        if widget.get_outer() == tree and widget.get_name() in buttons:
            widget.set_tool_tip_text(unreal.Text('1번 무기 · ' + buttons[widget.get_name()]))
    unreal.BlueprintEditorLibrary.compile_blueprint(menu)
    assert menu.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(menu, False)


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN)
    configure_fields(pawn)
    prop_mask = create_round_props(pawn)
    install_selection(pawn)
    bind_scope_ammo(pawn)
    install_reload(pawn, prop_mask)
    fit_loose_prop(pawn)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    defaults = unreal.get_default_object(pawn.generated_class())
    system = unreal.get_default_object(unreal.SystemLibrary)
    system.call_method('SetStringPropertyByName', (defaults, 'FurinaGameWeaponId', 'legacy'))
    system.call_method('SetIntPropertyByName', (defaults, 'FurinaGameCapacity', CLIP_SIZES['legacy']))
    assert ASSETS.save_loaded_asset(pawn, False)
    hide_weapon_hud()
    update_menu_tooltips()
    print('FPVM_PRIMARY_SAVED')


if __name__ == '__main__':
    main()
