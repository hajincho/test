"""Fire graph fixes in ThirdPersonCharacter_BP (EventGraph, nodes K2Node_FPF_*), 2026-11-15:
 1. aim point: ADS (iron sights) keeps the 50 m point of the sight line (camera ray); hip / shoulder (crosshair) now converge on the
    first thing the camera ray hits (ImpactPoint), 50 m point if it hits nothing -> the bullet lands on the crosshair at any range,
    no matter how far the muzzle is from the camera (3rd person shoulder camera: ~1 m).
 2. the elevation (drop compensation) follows the real aim distance: 0.000307 rad (50 m zero) * clamp(distance / 50 m, 0.2, 4).
 3. initial recoil: FurinaShotCount (int) counts the shots of a burst (reset when the fire input is released / cancelled);
    shots 1-4 get 120 % recoil (RecGain * 1.2), later shots 100 %.
Idempotent: nodes named FPN_* are only created once."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {'log': []}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def N(key): return nodes['K2Node_FPF_' + key]
    def fn(name, path):
        full = 'FPN_' + name
        n = nodes.get(full)
        if n is None:
            n = ed.add_call_function_node(path); assert n, path; n.rename(full); nodes[full] = n; R['log'].append('added ' + full)
        return n
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links()
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    ML = '/Script/Engine.KismetMathLibrary:'
    # ---- 1. aim point
    impact = N('BreakHit').find_output_pin('ImpactPoint')
    aimpt = N('AimPt'); w(impact, aimpt.find_input_pin('A'))
    end_pin = N('End').find_result_pin()
    final = fn('AimFinal', ML + 'SelectVector')
    w(end_pin, final.find_input_pin('A')); w(aimpt.find_result_pin(), final.find_input_pin('B'))
    ads_on = N('AdsOnF'); w(ads_on.find_result_pin(), final.find_input_pin('bPickA'))
    toaim = N('ToAim'); w(final.find_result_pin(), toaim.find_input_pin('A'))
    # ---- 2. elevation by aim distance
    dist = fn('AimDist', ML + 'VSize'); w(toaim.find_result_pin(), dist.find_input_pin('A'))
    per50 = fn('AimDist50', ML + 'Divide_DoubleDouble'); w(dist.find_result_pin(), per50.find_input_pin('A')); per50.find_input_pin('B').set_pin_value('5000')
    clamp = fn('AimDistClamp', ML + 'FClamp'); w(per50.find_result_pin(), clamp.find_input_pin('Value'))
    clamp.find_input_pin('Min').set_pin_value('0.2'); clamp.find_input_pin('Max').set_pin_value('4')
    elev = fn('AimElev', ML + 'Multiply_DoubleDouble'); w(clamp.find_result_pin(), elev.find_input_pin('A'))
    elev.find_input_pin('B').set_pin_value(N('Lift').find_input_pin('B').get_pin_value() if N('Lift').find_input_pin('B').get_pin_value() not in ('', '0') else '0.000307423')
    w(elev.find_result_pin(), N('Lift').find_input_pin('B'))
    # ---- 3. initial recoil
    var = 'FurinaShotCount'
    if var not in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
        assert ed.add_member_variable(var, unreal.BlueprintEditorLibrary.get_basic_type_by_name('int'), '0'); R['log'].append('added var')
    get = nodes.get('FPN_ShotCountGet') or ed.add_get_member_variable_node(var); get.rename('FPN_ShotCountGet'); nodes['FPN_ShotCountGet'] = get
    less = fn('ShotCountLess', ML + 'Less_IntInt'); w(get.find_output_pin(var), less.find_input_pin('A')); less.find_input_pin('B').set_pin_value('4')
    init = fn('InitRecoil', ML + 'SelectFloat'); init.find_input_pin('A').set_pin_value('1.2'); init.find_input_pin('B').set_pin_value('1.0')
    w(less.find_result_pin(), init.find_input_pin('bPickA'))
    gain2 = fn('RecGainInit', ML + 'Multiply_DoubleDouble'); w(N('RecGain').find_result_pin(), gain2.find_input_pin('A')); w(init.find_result_pin(), gain2.find_input_pin('B'))
    w(gain2.find_result_pin(), N('RecV').find_input_pin('B')); w(gain2.find_result_pin(), N('RecH').find_input_pin('B'))
    # count up after every shot (after the recoil kick), reset on fire release
    inc_n = nodes.get('FPN_ShotCountInc')
    if inc_n is None:
        inc_n = ed.add_set_member_variable_node(var); inc_n.rename('FPN_ShotCountInc'); nodes['FPN_ShotCountInc'] = inc_n
        add = fn('ShotCountAdd', ML + 'Add_IntInt'); w(get.find_output_pin(var), add.find_input_pin('A')); add.find_input_pin('B').set_pin_value('1')
        w(add.find_result_pin(), inc_n.find_input_pin(var))
        rec = N('Recoil'); old = list(rec.find_then_pin().list_connected_pins())
        rec.find_then_pin().break_pin_links(); w(rec.find_then_pin(), inc_n.find_execute_pin())
        for p in old: w(inc_n.find_then_pin(), p)
        rst = ed.add_set_member_variable_node(var); rst.rename('FPN_ShotCountReset'); nodes['FPN_ShotCountReset'] = rst
        rst.find_input_pin(var).set_pin_value('0')
        stop = N('Stop'); old2 = list(stop.find_then_pin().list_connected_pins())
        stop.find_then_pin().break_pin_links(); w(stop.find_then_pin(), rst.find_execute_pin())
        for p in old2: w(rst.find_then_pin(), p)
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\fp_aim_recoil_fix.json', 'w'), indent=1)
print('FP_AIM_RECOIL_FIX', R.get('status'), R.get('error', '')[:300])
