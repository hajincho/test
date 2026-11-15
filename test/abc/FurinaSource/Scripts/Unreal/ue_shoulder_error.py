"""Shoulder-fire inherent aim error (2026-11-15): while the shoulder stance (FurinaShoulder) is active and ADS is not, the bullet cone half angle (K2Node_FPF_Cone.ConeHalfAngleInDegrees)
gets  + atan(percent / 100) degrees  added after the stance / crouch multipliers: shots scatter uniformly over a disc whose radius is `percent` % of the distance to the aim point
(5 % -> 2.862 deg half angle; at 50 m: up to 2.5 m off, at 10 m: up to 0.5 m). usage: py ue_shoulder_error.py [percent]  (0 removes the error)"""
import unreal, json, traceback, sys, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
PCT = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
HIP_PCT = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0   # un-aimed (hip) fire; ADS has no added error
def main():
    R = {}
    bp = unreal.load_asset(CH)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    deg = math.degrees(math.atan(PCT / 100.0)); R['deg'] = deg
    hip_deg = math.degrees(math.atan(HIP_PCT / 100.0)); R['hip_deg'] = hip_deg
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    def call(name, path):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name); return n
    if 'FPN_ShErrSel' not in nodes:
        nt = call('FPN_ShErrNotAds', '/Script/Engine.KismetMathLibrary:Not_PreBool'); w(nodes['K2Node_FPF_AdsOnF'].find_result_pin(), nt.find_input_pin('A'))
        an = call('FPN_ShErrAnd', '/Script/Engine.KismetMathLibrary:BooleanAND'); w(nodes['K2Node_FPF_ShOnF'].find_result_pin(), an.find_input_pin('A')); w(nt.find_result_pin(), an.find_input_pin('B'))
        sel = call('FPN_ShErrSel', '/Script/Engine.KismetMathLibrary:SelectFloat'); sel.find_input_pin('B').set_pin_value('0.0')
        w(an.find_result_pin(), sel.find_input_pin('bPickA'))
        add = call('FPN_ShErrAdd', '/Script/Engine.KismetMathLibrary:Add_DoubleDouble')
        w(nodes['K2Node_FPF_CrouchCone'].find_result_pin(), add.find_input_pin('A')); w(sel.find_result_pin(), add.find_input_pin('B'))
        w(add.find_result_pin(), nodes['K2Node_FPF_Cone'].find_input_pin('ConeHalfAngleInDegrees'))
        R['added'] = True
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FPN_ShErrOuter' not in nodes:
        # rev. b: error = ADS ? 0 : (shoulder ? shoulder% : hip%)   (Sel now picks by the shoulder flag directly; the Not/And nodes from rev. a stay unused)
        sel = nodes['FPN_ShErrSel']; w(nodes['K2Node_FPF_ShOnF'].find_result_pin(), sel.find_input_pin('bPickA'))
        out = call('FPN_ShErrOuter', '/Script/Engine.KismetMathLibrary:SelectFloat'); out.find_input_pin('A').set_pin_value('0.0')
        w(nodes['K2Node_FPF_AdsOnF'].find_result_pin(), out.find_input_pin('bPickA')); w(sel.find_result_pin(), out.find_input_pin('B'))
        w(out.find_result_pin(), nodes['FPN_ShErrAdd'].find_input_pin('B'))
        nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    nodes['FPN_ShErrSel'].find_input_pin('A').set_pin_value('%.6f' % deg)
    nodes['FPN_ShErrSel'].find_input_pin('B').set_pin_value('%.6f' % hip_deg)
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\shoulder_error.json', 'w'), indent=1); print('SHOULDER_ERROR', R)
