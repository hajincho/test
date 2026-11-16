"""Weapon dispersion (2026-11-16): the user wants shots to land RANDOMLY inside a circle of 1 m diameter at 500 m ('realism') - not an extra bullet drop. So
 1. the drag change of the previous turn is reverted: K2Node_FPB_Kv.B -> 1.4261805540956367e-05 /cm (k = ln(988/920)/50 per m) in BP_FurinaBullet and FPN_AimElev.B -> 0.000307423138019658 (50 m compensation) in the character BP;
 2. the base spread cone (half angle, uniform inside the cone = uniform inside the circle on a target) is set so that a standing, still, ADS shot has half angle atan(0.5 m / 500 m) = 0.0572958 deg:
    K2Node_FPF_SprBase.B = 0.0572958 / 0.9 (the ADS multiplier 0.9 stays) = 0.0636620 (was 0.15, i.e. 2.4 m diameter at 500 m). Hip / shoulder multipliers (1.10 / 1.05), the walking term (0.0015 deg per cm/s),
    the crouch / prone multipliers and the hip / shoulder aim error cones (3 % / 1 %) are unchanged.   -> Data/spread_500.json (PIE stopped)"""
import unreal, json, os, math, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
HALF = math.degrees(math.atan(0.5 / 500.0)); BASE = HALF / 0.9
def main():
    R = {'half_deg_at_500m': HALF, 'base': BASE}
    E = unreal.EditorAssetLibrary
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    p = nodes['K2Node_FPB_Kv'].find_input_pin('B'); R['kv_before'] = p.get_pin_value(); p.set_pin_value('1.4261805540956367e-05'); R['kv_after'] = p.get_pin_value()
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['bullet_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['bullet_saved'] = E.save_loaded_asset(bp, False)
    del bp
    ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ch, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for name, pin, val in (('FPN_AimElev', 'B', '0.000307423138019658'), ('K2Node_FPF_SprBase', 'B', repr(BASE))):
        pn = nodes[name].find_input_pin(pin); R.setdefault('before', {})[name] = pn.get_pin_value(); assert pn.set_pin_value(val); R.setdefault('after', {})[name] = pn.get_pin_value()
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(ch); R['char_status'] = str(ch.get_editor_property('status'))
    if ch.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = E.save_loaded_asset(ch, False)
    del ch
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'spread_500.json'), 'w'), indent=1); print('SPREAD_500', R.get('error', R.get('char_status'))[-300:])
