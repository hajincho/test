"""PIE: sets the character's HUD-relevant variables to test the HUD. usage: py ue_hud_force.py <ammo> <reserve> <reloading 0|1>"""
import unreal, sys
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_character(w, 0)
pc.set_editor_property('FurinaAmmo', int(sys.argv[1])); pc.set_editor_property('FurinaReserve', int(sys.argv[2])); pc.set_editor_property('FurinaReloading', sys.argv[3] == '1')
print('HUD_FORCE', pc.get_editor_property('FurinaAmmo'), pc.get_editor_property('FurinaReserve'), pc.get_editor_property('FurinaReloading'))
del w, pc
