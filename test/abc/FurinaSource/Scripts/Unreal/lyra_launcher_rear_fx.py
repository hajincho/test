"""Use the shared Niagara burst with a smaller visual scale behind launchers."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import Graph, PAWN, literal, wire


SYSTEM = '/Game/Effects/Particles/Explosion/NS_Grenade_Explosion.NS_Grenade_Explosion'
REAR_VISUAL_SCALE = '0.28,0.36,0.24'


def install(pawn):
    graph = Graph(pawn)
    burst = graph.nodes['LCH_RearNS']
    literal(burst, 'SystemTemplate', SYSTEM)
    literal(burst, 'Scale', REAR_VISUAL_SCALE)
    # Retire setters that belonged to the muzzle-flash system.
    shell = graph.nodes.get('LCH_RearNSShell')
    if not shell:
        return
    next_ = list(shell.find_then_pin().list_connected_pins())
    if next_:
        shell.find_then_pin().break_pin_links()
        burst.find_then_pin().break_pin_links()
        for destination in next_:
            wire(burst.find_then_pin(), destination)


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing weapon effects'
    pawn = unreal.load_asset(PAWN)
    install(pawn)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
    print('LAUNCHER_REAR_NIAGARA_SAVED')


if __name__ == '__main__':
    main()
