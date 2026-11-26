"""Import the revised in-game pickup clips and synchronize the reload timer."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_clip, import_pistol
from lyra_fpvm_optics import Graph, literal, PAWN
from lyra_pzb39 import ASSETS, FOLDER, save


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world()
    world = editor.get_editor_world()
    setting = 'Interchange.FeatureFlags.Import.FBX'
    old = unreal.SystemLibrary.get_console_variable_bool_value(setting)
    unreal.SystemLibrary.execute_console_command(world, setting + ' 0')
    lengths = set()
    try:
        import_pistol('pzb39')
        mesh = unreal.load_asset(FOLDER + '/SK_FPVM_PZB39')
        ammo = unreal.load_asset('/Game/Furina/Weapons/Germany/ammo_7_92x94/SM_DE_ammo_7_92x94')
        defaults = {str(slot.material_slot_name): slot.material_interface for slot in ammo.static_materials}
        defaults['Primer_Metal008'] = unreal.load_asset(FOLDER + '/M_PZB39_Primer_Metal008')
        materials = list(mesh.materials)
        applied = set()
        for slot in materials:
            key = str(slot.material_slot_name)
            if key in defaults:
                assert defaults[key], key
                slot.material_interface = defaults[key]
                applied.add(key)
        assert applied == set(defaults), applied
        mesh.set_editor_property('materials', materials)
        assert ASSETS.save_loaded_asset(mesh, False)
        skeleton = mesh.get_editor_property('skeleton')
        variations = [f'ReloadR{n:02}' for n in range(1, 11)]
        for suffix in variations:
            asset = import_clip(FOLDER, skeleton, 'AS_FPVM_PZB39_' + suffix)
            assert ASSETS.save_loaded_asset(asset, False), suffix
            lengths.add(asset.get_play_length())
    finally:
        unreal.SystemLibrary.execute_console_command(world, setting + (' 1' if old else ' 0'))
    seconds, = lengths
    pawn = unreal.load_asset(PAWN)
    graph = Graph(pawn)
    for name in ('Pzb39_ReloadTime', 'Pzb39_ReloadLength'):
        literal(graph.nodes[name], 'FurinaVMReloadLen', seconds)
    save(pawn)
    print('PZB39_HAND_TRACKS_SAVED', seconds)


if __name__ == '__main__':
    main()
