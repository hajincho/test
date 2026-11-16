"""Editor (PIE stopped): the bundle's Grind_Rail_Component_BP has UsingRail? = True as a stale class default and only resets it when its tick runs near rails. In the tunnel level (no 'Rail' tagged meshes) it stays True,
which turns FurinaSpecial on (forces third person, blocks firing). Sets the class default UsingRail? / UsingZipline? / RailJumpActive? = False, compiles and saves the component blueprint -> Data/grind_default_false.json"""
import unreal, json, traceback
R = {}
try:
    P = '/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP'
    bp = unreal.load_asset(P); cdo = unreal.get_default_object(bp.generated_class())
    for p in ('UsingRail?', 'UsingZipline?', 'RailJumpActive?', 'WasUsingRail?'):
        R[p + '_before'] = bool(cdo.get_editor_property(p)); cdo.set_editor_property(p, False)
    try: bp.get_package().set_dirty_flag(True)
    except Exception as e: R['dirty_err'] = str(e)[:80]
    try: unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['compiled'] = True
    except Exception as e: R['compile_err'] = str(e)[:80]
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    bp2 = unreal.load_asset(P); R['after_reload'] = bool(unreal.get_default_object(bp2.generated_class()).get_editor_property('UsingRail?'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\grind_default_false.json', 'w'), indent=1); print('GRIND_DEFAULT', R)
