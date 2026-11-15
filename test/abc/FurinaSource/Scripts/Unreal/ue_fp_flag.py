"""PIE helper: set a tagged flag component on the player character. usage: py ue_fp_flag.py <Tag> <0|1>"""
import unreal, sys
def main():
    tag, on = sys.argv[1], sys.argv[2] == '1'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    comps = pawn.get_components_by_tag(unreal.ActorComponent, tag)
    for c in comps: c.set_active(on, False)
    print('FP_FLAG', tag, on, len(comps))
    del w, pawn, comps
main()
del main
