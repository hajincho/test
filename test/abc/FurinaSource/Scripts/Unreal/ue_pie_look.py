"""PIE: set the player's control rotation. usage: py ue_pie_look.py <yaw> [pitch]"""
import unreal, sys
def main():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=float(sys.argv[2]) if len(sys.argv) > 2 else 0.0, yaw=float(sys.argv[1])))
    print('PIE_LOOK', pc.get_control_rotation())
    del w, pc
main(); del main
