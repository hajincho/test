"""After the rifle swap to the Colt M4A1 (2026-11-15): updates the rifle-local calibration points in ThirdPersonCharacter_BP from Data/colt_geometry.json
(rear aperture / front post -> FPN_SightRear / FPN_SightFront, muzzle flash point M4_FlashPoint, empty case ejection M4_CasePoint) and sets the ammo to magazine 20 / reserve 600
(TFP_MagRoom A = 20, defaults FurinaAmmo 20 / FurinaReserve 600, also on the level instance). Run with PIE stopped."""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
G = json.load(open(os.path.join(D, 'colt_geometry.json')))
def v(p): return ','.join(repr(float(x)) for x in p)
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def setpin(node, pin, value):
        n = nodes[node]; p = n.find_input_pin(pin); assert p.is_valid(), (node, pin); R.setdefault('before', {})[node + '.' + pin] = p.get_pin_value(); p.set_pin_value(value); R.setdefault('after', {})[node + '.' + pin] = p.get_pin_value()
    setpin('FPN_SightRear', 'Location', v(G['rear_aperture']))
    setpin('FPN_SightFront', 'Location', v(G['front_post']))
    setpin('M4_FlashPoint', 'Location', v(G['muzzle']))
    setpin('M4_CasePoint', 'Location', v(G['case_port']))
    setpin('TFP_MagRoom', 'A', '20')
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    cdo = unreal.get_default_object(bp.generated_class())
    R['cdo_before'] = [cdo.get_editor_property('FurinaAmmo'), cdo.get_editor_property('FurinaReserve')]
    cdo.set_editor_property('FurinaAmmo', 20); cdo.set_editor_property('FurinaReserve', 600)
    R['cdo_after'] = [cdo.get_editor_property('FurinaAmmo'), cdo.get_editor_property('FurinaReserve')]
    for a in unreal.EditorLevelLibrary.get_all_level_actors():      # level instances inherit the defaults (the variables are not instance-editable); only report them
        if a.get_class() == bp.generated_class(): R.setdefault('level_values', []).append([a.get_editor_property('FurinaAmmo'), a.get_editor_property('FurinaReserve')])
    if R['status'] != 'BlueprintStatus.BS_ERROR': R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp, cdo
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'colt_calibrate.json'), 'w'), indent=1); print('COLT_CALIBRATE', R.get('error', R.get('status')))
