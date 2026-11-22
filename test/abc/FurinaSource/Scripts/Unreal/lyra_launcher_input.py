"""Route launcher presses through the existing shot event immediately."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, wire


def install(pawn):
    g = Graph(pawn, 'LauncherInput_')
    if 'LauncherInput_FireOnPress' in g.nodes:
        return

    timer = g.nodes['K2Node_FPF_Auto'].find_execute_pin()
    started = g.nodes['K2Node_FPF_FireIA'].find_output_pin('Started')
    assert timer in started.list_connected_pins()

    # A released button stops the repeat timer. A launcher press has no repeat
    # timer, and still passes through the shared shot event's normal gates.
    secondary = g.call('SecondarySelected', ENGINE + 'ActorComponent:IsActive',
                       target=g.get('FurinaPistolOn')).find_result_pin()
    primary = g.call('PrimarySelected', MATH + 'Not_PreBool', A=secondary).find_result_pin()
    launcher = g.nodes['LCH_FireIsL'].find_output_pin('ReturnValue')
    should_fire = g.call('Direct', MATH + 'BooleanAND', A=launcher, B=primary).find_result_pin()
    branch = g.branch('Choose', should_fire)
    callback = pawn.generated_class().get_path_name() + ':FurinaRifleShot'
    shot = g.call('FireOnPress', callback)
    timer.break_pin_links()
    wire(started, branch.find_execute_pin())
    wire(branch.find_else_pin(), timer)
    wire(branch.find_then_pin(), shot.find_execute_pin())


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing the weapon input graph'
    pawn = unreal.load_asset(PAWN)
    install(pawn)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn, False)
    print('LAUNCHER_INPUT_SAVED')


if __name__ == '__main__':
    main()
