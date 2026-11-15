"""ADS fire direction from the iron sights themselves (2026-11-15). In ADS the aim point is no longer the camera ray: it is the point 50 m along the line
rear aperture centre -> front post tip, both transformed with the live rifle component transform (so recoil kick, cant and bob are included).
The bullet still leaves the muzzle and crosses that line at 50 m. Sight points in the SK_M4A1 mesh space (Data/m4_sights_refine.json):
rear aperture centre (0.139, -11.757, 9.957) (circle fit of the rear plane), front post tip (0.081, 30.682, 9.815)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
REAR, FRONT = '0.139,-11.757165,9.957', '0.080865,30.682121,9.815'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    ML = '/Script/Engine.KismetMathLibrary:'
    def fn(name, path):
        n = nodes.get('FPN_' + name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename('FPN_' + name); nodes['FPN_' + name] = n; R.setdefault('added', []).append(name)
        return n
    def w(a, b):
        assert a.is_valid() and b.is_valid(); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    xf = nodes['K2Node_FPF_RifleXf'].find_result_pin()
    rear = fn('SightRear', ML + 'TransformLocation'); w(xf, rear.find_input_pin('T')); rear.find_input_pin('Location').set_pin_value(REAR)
    front = fn('SightFront', ML + 'TransformLocation'); w(xf, front.find_input_pin('T')); front.find_input_pin('Location').set_pin_value(FRONT)
    diff = fn('SightDiff', ML + 'Subtract_VectorVector'); w(front.find_result_pin(), diff.find_input_pin('A')); w(rear.find_result_pin(), diff.find_input_pin('B'))
    nrm = fn('SightDir', ML + 'Normal'); w(diff.find_result_pin(), nrm.find_input_pin('A')); nrm.find_input_pin('Tolerance').set_pin_value('0.0001')
    far = fn('Sight50', ML + 'Multiply_VectorFloat'); w(nrm.find_result_pin(), far.find_input_pin('A')); far.find_input_pin('B').set_pin_value('5000')
    pt = fn('SightPoint', ML + 'Add_VectorVector'); w(rear.find_result_pin(), pt.find_input_pin('A')); w(far.find_result_pin(), pt.find_input_pin('B'))
    w(pt.find_result_pin(), nodes['FPN_AimFinal'].find_input_pin('A'))     # AimFinal: A (ADS) = sight point, B = crosshair point
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\fp_sight_aim.json', 'w'), indent=1); print('FP_SIGHT_AIM', R)
