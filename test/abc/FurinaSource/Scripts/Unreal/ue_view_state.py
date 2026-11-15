"""PIE: prints the view / ADS flags (FPCamera active, FurinaFPWanted, FurinaADS, FurinaADSRestoreTP) -> appends to Data/view_state.json (key = tag). usage: py ue_view_state.py <tag>"""
import unreal, json, os, sys
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\view_state.json'
tag = sys.argv[1] if len(sys.argv) > 1 else 'x'
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
def f(t): c = pc.get_components_by_tag(unreal.ActorComponent, t); return bool(c and c[0].is_active())
R = dict(fp_camera=bool(pc.get_editor_property('FPCamera').is_active()), fp_wanted=bool(pc.get_editor_property('FurinaFPWanted').is_active()), ads=f('FurinaADS'), restore_tp=f('FurinaADSRestoreTP'))
d = json.load(open(OUT)) if os.path.exists(OUT) else {}; d[tag] = R; json.dump(d, open(OUT, 'w'), indent=1); print('VIEW_STATE', tag, R)
del w, pc
