"""Give PzB 39 its own ten-round case and replace it only from the weapon menu."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_clip, import_pistol
from lyra_fpvm_optics import ENGINE, MATH, PAWN, STRINGS, Graph, chain, relay, wire
from lyra_fpvm_primary import constant
from lyra_pzb39 import API, ASSETS, FOLDER, save


RESERVE = 'FurinaPzbReserve'
REQUEST = 'FurinaPzbMenuRequested'
DISPLAY = 'FurinaPzb39CaseRefresh'
MENU = '/Game/Furina/UI/WBP_FurinaWeaponMenu'
SYSTEM = ENGINE + 'KismetSystemLibrary:'


def fields(pawn):
    existing = {str(name) for name in API.list_member_variable_names(pawn)}
    for name, category in ((RESERVE, 'int'), (REQUEST, 'bool')):
        if name not in existing:
            assert API.add_member_variable(pawn, name, API.get_basic_type_by_name(category))
    API.compile_blueprint(pawn)
    unreal.get_default_object(pawn.generated_class()).set_editor_property(RESERVE, 10)


def install_pawn(pawn):
    graph = Graph(pawn, 'PzbAmmo_')
    if 'PzbAmmo_LoadFromCase' in graph.nodes:
        return
    owner = graph.nodes['K2Node_FPF_Self'].find_output_pin('self')
    vm = graph.get('FurinaFPVM')
    rounds = graph.get(RESERVE)

    def outcome(name, function, **args):
        return graph.call(name, function, **args).find_result_pin()

    def math_(name, function, **args):
        return outcome(name, MATH + function, **args)

    def number(name, n):
        return constant(graph, name, n)

    def equal(name, field):
        return outcome(name, STRINGS + 'EqualEqual_StrStr', A=graph.get(field), B='pzb39')

    def refresh(name):
        return graph.call(name, pawn.generated_class().get_path_name() + ':' + DISPLAY)

    is_pzb = equal('IsEquipped', 'FurinaGameWeaponId')
    uses_case = graph.nodes['HistoryReload_Transfer'].find_input_pin('B')
    old_source, = uses_case.list_connected_pins()
    uses_case.break_pin_links()
    supply = math_('LoadFromCase', 'SelectInt', bPickA=is_pzb, A=rounds, B=old_source)
    wire(supply, uses_case)

    # Debit the case when the shared reload finishes. Other equipment keeps its original reserve.
    completed = graph.nodes['M4_FillMagazine'].find_then_pin()
    normal = graph.nodes['TFP_SetFurinaReserve'].find_execute_pin()
    completed.break_pin_links()
    debit = graph.branch('UseOwnReserve', is_pzb)
    wire(completed, debit.find_execute_pin())
    wire(debit.find_else_pin(), normal)
    remainder = math_('Remaining', 'Subtract_IntInt', A=rounds, B=graph.get('FurinaReloadAmount'))
    update = graph.store('Debit', RESERVE, math_('ClampRemaining', 'Max', A=remainder, B=number('Zero', 0)))

    # Show the remaining case slots after selection, commitment, or a fresh Tab issue.
    event = graph.editor.add_custom_event_node(DISPLAY)
    event.rename('PzbAmmo_RefreshEvent')
    tail = [event.find_then_pin()]
    skinned = ENGINE + 'SkinnedMeshComponent:'
    for count in range(1, 11):
        bone = f'VM_Ammo_{count:02}'
        visible = math_(f'HasSlot{count}', 'GreaterEqual_IntInt', A=rounds, B=number(f'Slot{count}', count))
        branch = graph.branch(f'InspectSlot{count}', visible)
        show = graph.call(f'ShowSlot{count}', skinned + 'UnHideBoneByName', vm, BoneName=bone)
        hide = graph.call(f'HideSlot{count}', skinned + 'HideBoneByName', vm, BoneName=bone, PhysBodyOption='PBO_None')
        for source in tail:
            wire(source, branch.find_execute_pin())
        wire(branch.find_then_pin(), show.find_execute_pin())
        wire(branch.find_else_pin(), hide.find_execute_pin())
        tail = [show.find_then_pin(), hide.find_then_pin()]
    API.compile_blueprint(pawn)
    wire(chain(debit.find_then_pin(), [update, refresh('RepaintUsedSlot')]), graph.nodes['M4_ReloadDone'].find_execute_pin())

    assigned = next(node for name, node in graph.nodes.items() if name.startswith('Pzb39_SaveRounds_pzb39_'))
    for _ in range(3):
        connection, = assigned.find_then_pin().list_connected_pins()
        assigned = connection.get_owning_node()
    equip_display = refresh('RepaintEquippedCase')
    relay(assigned.find_then_pin(), equip_display.find_execute_pin(), equip_display.find_then_pin())

    selection = graph.nodes['Pzb39_ReloadSelected'].find_then_pin()
    default_clip = graph.nodes['Pzb39_ReloadClip']
    set_length = graph.nodes['Pzb39_ReloadLength'].find_execute_pin()
    selection.break_pin_links()
    for count in range(1, 11):
        match = math_(f'PickSlot{count}', 'EqualEqual_IntInt', A=rounds, B=number(f'Match{count}', count))
        branch = graph.branch(f'SlotClip{count}', match)
        asset = unreal.load_asset(f'{FOLDER}/AS_FPVM_PZB39_ReloadR{count:02}')
        assert asset
        clip = graph.store(f'ReloadCase{count}', 'FurinaVMAnimReload', asset)
        wire(selection, branch.find_execute_pin())
        wire(chain(branch.find_then_pin(), [clip]), set_length)
        selection = branch.find_else_pin()
    wire(selection, default_clip.find_execute_pin())

    not_reloading = math_('ReloadComplete', 'Not_PreBool', A=graph.get('FurinaReloading'))
    not_falling = math_('RecoveryComplete', 'Not_PreBool', A=graph.get('FurinaPzbBusy'))
    eligible = math_('NotBusy', 'BooleanAND', A=not_reloading, B=not_falling)
    same = math_('SelectionApplied', 'BooleanAND', A=is_pzb, B=equal('StillSelected', 'FurinaPrimaryKey'))
    requested = math_('RefillRequested', 'BooleanAND', A=graph.get(REQUEST), B=same)
    grant = graph.branch('IssueFromMenu', math_('CanIssue', 'BooleanAND', A=eligible, B=requested))
    destination = graph.nodes['ScopeView_HideViewmodel'].find_execute_pin()
    previous = list(destination.list_connected_pins())
    destination.break_pin_links()
    for source in previous:
        wire(source, grant.find_execute_pin())
    wire(grant.find_else_pin(), destination)
    fresh = [
        graph.store('ConsumeRequest', REQUEST, False),
        graph.store('FullCase', RESERVE, 10),
        graph.store('RoundReady', 'FurinaAmmo', 1),
        graph.store('ClearBusy', 'FurinaVMBusy', 0.),
        graph.store('RestartIdle', 'FurinaVMIdle', False),
        refresh('RepaintFreshCase'),
    ]
    wire(chain(grant.find_then_pin(), fresh), destination)


def install_menu():
    asset = unreal.load_asset(MENU)
    graph = Graph(asset, 'PzbAmmo_')
    graph.editor = unreal.BlueprintGraphEditor.get_graph_editor_by_name(asset, 'OnPreviewMouseButtonDown')
    nodes = {node.get_name(): node for node in graph.editor.list_all_nodes()}
    if 'PzbAmmo_TabFresh' not in nodes:
        entry = next(node for name, node in nodes.items() if name.startswith('WS_K_')
                     and str(node.find_input_pin('Value').get_pin_value()) == 'pzb39')
        player, = entry.find_input_pin('Object').list_connected_pins()
        fresh = graph.call('TabFresh', SYSTEM + 'SetBoolPropertyByName', Object=player, PropertyName=REQUEST, Value=True)
        relay(entry.find_then_pin(), fresh.find_execute_pin(), fresh.find_then_pin())
    tree = unreal.find_object(None, MENU + '.WBP_FurinaWeaponMenu:WidgetTree')
    for widget in unreal.ObjectIterator(unreal.Button):
        if widget.get_outer() == tree and widget.get_name() == 'Btn_0_3_2':
            widget.set_tool_tip_text(unreal.Text('PzB 39 · 7.92×94 · 약실 1발 + 탄약함 10발'))
            break
    save(asset)


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world()
    world = editor.get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    prior = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        import_pistol('pzb39')
        skeleton = unreal.load_asset(f'{FOLDER}/SK_FPVM_PZB39').get_editor_property('skeleton')
        for count in range(1, 11):
            sequence = import_clip(FOLDER, skeleton, f'AS_FPVM_PZB39_ReloadR{count:02}')
            assert ASSETS.save_loaded_asset(sequence, False)
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if prior else ' 0'))

    pawn = unreal.load_asset(PAWN)
    fields(pawn)
    install_pawn(pawn)
    save(pawn)
    install_menu()
    print('PZB39_FINITE_AMMUNITION_SAVED')


if __name__ == '__main__':
    main()
