"""Fix (2026-11-15): FPN_Sight50 became a 'vector * vector' node whose B pin stayed 0,0,0, so SightPoint = the rear sight itself and ADS bullets were aimed at a point behind the
muzzle (flew backwards into the shooter, yaw error 180 deg in Data/ads_sight_probe.json). B is now 5000,5000,5000 (50 m)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    n = next(x for x in ed.list_all_nodes() if x.get_name() == 'FPN_Sight50')
    p = n.find_input_pin('B'); R['before'] = p.get_pin_value(); p.set_pin_value('5000,5000,5000'); R['after'] = p.get_pin_value()
    del ed, n, p
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\fp_sight_fix.json', 'w'), indent=1); print('SIGHT_FIX', R)
