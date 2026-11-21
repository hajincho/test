"""Keep M4 visuals and the legacy HUD out of the historical first-person view."""
import json
from pathlib import Path

import unreal


PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
HUD = '/Game/Furina/FP/BP_FurinaHUD'
PREFIX = 'HistoricalView_'


def wire(source, target):
    assert source.is_valid() and target.is_valid()
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(source, target)


def add_call(graph, name, function):
    node = graph.add_call_function_node(function)
    assert node, function
    node.rename(PREFIX + name)
    return node


def add_branch(graph, name, condition):
    node = graph.add_branch_node()
    node.rename(PREFIX + name)
    wire(condition, node.find_input_pin('Condition'))
    return node


def insert_filter(graph, name, condition, first, alternate=None):
    """Route normal M4 execution through first, or bypass the legacy visual."""
    start = first.find_execute_pin()
    sources = list(start.list_connected_pins())
    assert sources, first.get_name()
    branch = add_branch(graph, name, condition)
    start.break_pin_links()
    for source in sources:
        wire(source, branch.find_execute_pin())
    wire(branch.find_else_pin(), start)
    if alternate:
        wire(branch.find_then_pin(), alternate.find_execute_pin())


def patch_pawn(pawn):
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph')
    nodes = {node.get_name(): node for node in graph.list_all_nodes()}
    if PREFIX + 'HideRifle' in nodes:
        return

    # Animation ticks continue to set Visibility on the bolt, handle, and magazine.
    # HiddenInGame is a separate flag, so those writes cannot expose the M4 again.
    view = next(node for name, node in nodes.items() if name.startswith('VM_VisVM_'))
    transition = next(node for name, node in nodes.items() if name.startswith('VM_VisRifle_'))
    visible = view.find_input_pin('bNewVisibility').list_connected_pins()[0]
    previous = transition.find_then_pin()
    continuation = list(previous.list_connected_pins())
    assert len(continuation) == 1
    previous.break_pin_links()
    for component in ('Rifle', 'Bolt', 'Handle', 'Mag', 'SlingM4', 'FPArmL', 'FPArmR'):
        variable = 'Furina' + component
        getter = graph.add_get_member_variable_node(variable)
        assert getter, variable
        hide = add_call(graph, 'Hide' + component, '/Script/Engine.SceneComponent:SetHiddenInGame')
        wire(getter.find_output_pin(variable), hide.find_self_pin())
        wire(visible, hide.find_input_pin('NewHidden'))
        wire(previous, hide.find_execute_pin())
        previous = hide.find_then_pin()
    wire(previous, continuation[0])

    vm_on = graph.add_get_member_variable_node('FurinaVMOn').find_output_pin('FurinaVMOn')
    # A dropped magazine is a new actor and is unaffected by component visibility.
    insert_filter(graph, 'DropOnlyM4', vm_on, nodes['FMG_DropSpawn'], nodes['FMG_HideMag'])
    insert_filter(graph, 'EjectOnlyM4', vm_on, nodes['M4_CaseSpawn'], nodes['P2_Branch_8e47b848'])


def patch_hud(hud, pawn_class):
    graph = unreal.BlueprintGraphEditor.get_graph_editor_by_name(hud, 'EventGraph')
    nodes = {node.get_name(): node for node in graph.list_all_nodes()}
    if PREFIX + 'DrawOnlyLegacy' in nodes:
        return
    cast = nodes['M4HUD_Cast']
    player = next(pin for pin in cast.list_output_pins() if str(pin.get_pin_name()).startswith('As'))
    getter = graph.add_get_member_variable_node('FurinaVMOn', pawn_class.get_path_name())
    wire(player, getter.find_self_pin())
    # The weapon HUD draws its frame, ammo, reload indicators and crosshair from this chain.
    insert_filter(graph, 'DrawOnlyLegacy', getter.find_output_pin('FurinaVMOn'), nodes['FHUD_SetAmmo'])


def main():
    root = Path(unreal.Paths.project_dir()).resolve()
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN)
    hud = unreal.load_asset(HUD)
    patch_pawn(pawn)
    patch_hud(hud, pawn.generated_class())
    for asset in (pawn, hud):
        unreal.BlueprintEditorLibrary.compile_blueprint(asset)
        assert asset.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, asset.get_name()
    for asset in (pawn, hud):
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False), asset.get_name()
    (root / 'Saved' / 'FPVMVisibilitySaved.json').write_text(json.dumps({'saved': [PAWN, HUD]}), encoding='utf-8')


if __name__ == '__main__':
    main()
