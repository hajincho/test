"""Import and equip the PzB 39 using the existing primary weapon graph."""
import json
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_pistol
from lyra_fpvm_optics import ENGINE, PAWN, STRINGS, Graph, chain, literal, wire
from lyra_fpvm_primary import CLIP_SIZES, weapon_ammo


ASSETS = unreal.EditorAssetLibrary
API = unreal.BlueprintEditorLibrary
FOLDER = '/Game/Furina/FPVM/PZB39'
ROOT = Path(unreal.Paths.project_dir()).resolve()


def display_alignment():
    path = ROOT / 'FurinaSource/Data/pzb39_display_alignment.json'
    if not path.is_file():
        return '2,-9.6,2.3', '0.5,2.3,2'
    data = json.loads(path.read_text(encoding='utf-8'))
    turn = unreal.Quat(*data['ue_quat_xyzw']).rotator()
    return ','.join(map(str, data['ue_loc_cm'])), f'{turn.pitch},{turn.yaw},{turn.roll}'


def insert(source, branch):
    previous = list(source.list_connected_pins())
    source.break_pin_links()
    wire(source, branch.find_execute_pin())
    for target in previous:
        wire(branch.find_else_pin(), target)


def matches(graph, name, field):
    return graph.branch(name, graph.call(name + 'Key', STRINGS + 'EqualEqual_StrStr',
                                         A=graph.get(field), B='pzb39').find_result_pin())


def install_weapon(pawn):
    graph = Graph(pawn, 'Pzb39_')
    if 'Pzb39_Equip' in graph.nodes:
        return
    vm = graph.get('FurinaFPVM')
    branch = matches(graph, 'Selected', 'FurinaPrimaryKey')
    insert(graph.locate('VW_S_7_').find_then_pin(), branch)
    mesh = unreal.load_asset(FOLDER + '/SK_FPVM_PZB39')
    clips = {clip: unreal.load_asset(f'{FOLDER}/AS_FPVM_PZB39_{clip}') for clip in ('Idle', 'Fire', 'Reload')}
    location, rotation = display_alignment()
    actions = [
        graph.call('Equip', ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', vm, NewMesh=mesh),
        *[graph.call(f'ResetMaterial_{slot}', ENGINE + 'PrimitiveComponent:SetMaterial', vm, ElementIndex=slot)
          for slot in range(10)],
        *[graph.store(clip, 'FurinaVMAnim' + clip, asset) for clip, asset in clips.items()],
        graph.store('ADSLocation', 'FurinaVMAdsLoc', location),
        graph.store('ADSRotation', 'FurinaVMAdsRot', rotation),
        graph.store('FireTime', 'FurinaVMFireLen', clips['Fire'].get_play_length()),
        graph.store('ReloadTime', 'FurinaVMReloadLen', clips['Reload'].get_play_length()),
        graph.store('NoScope', 'FurinaScopeZoom', 1.),
        graph.store('Valid', 'FurinaVMValid', True),
    ]
    CLIP_SIZES['pzb39'] = 1
    downstream = graph.locate('VM_Br_12_').find_execute_pin()
    weapon_ammo(graph, chain(branch.find_then_pin(), actions), 'pzb39', downstream)

    reload_branch = matches(graph, 'ReloadSelected', 'FurinaGameWeaponId')
    insert(graph.nodes['HistoryReload_Choose_pp'].find_else_pin(), reload_branch)
    reload_actions = [
        graph.store('ReloadClip', 'FurinaVMAnimReload', clips['Reload']),
        graph.store('ReloadLength', 'FurinaVMReloadLen', clips['Reload'].get_play_length()),
        graph.store('ReloadLoose', 'FurinaLooseReload', False),
    ]
    wire(chain(reload_branch.find_then_pin(), reload_actions), graph.nodes['HistoryReload_PrepareProp'].find_execute_pin())


def save(pawn):
    API.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(pawn, False)


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    if not ASSETS.does_asset_exist(FOLDER + '/SK_FPVM_PZB39'):
        enabled = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
        unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), cvar + ' 0')
        try:
            print('PZB39_IMPORTED', import_pistol('pzb39'))
        finally:
            unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), cvar + (' 1' if enabled else ' 0'))
    pawn = unreal.load_asset(PAWN)
    install_weapon(pawn)
    graph = Graph(pawn)
    location, rotation = display_alignment()
    literal(graph.nodes['Pzb39_ADSLocation'], 'FurinaVMAdsLoc', location)
    literal(graph.nodes['Pzb39_ADSRotation'], 'FurinaVMAdsRot', rotation)
    save(pawn)
    print('PZB39_EQUIP_SAVED')


if __name__ == '__main__':
    main()
