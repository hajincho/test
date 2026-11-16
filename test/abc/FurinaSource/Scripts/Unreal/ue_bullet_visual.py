"""Visible bullet + M4A1 ballistics refresh (2026-11-16). PIE stopped.
 1. BP_FurinaBullet: the bullet-shaped mesh SM_223Projectile (cut from the 223-remington asset earlier) is now drawn BIG enough to see (relative scale argv[1], default 20 -> ~25 cm long, 11 cm thick; the real round is 1.3 cm) with the hot
    unlit material M_BulletGlow (copper-gold emissive); the tracer streak behind it is unchanged.
 2. Air drag: K2Node_FPB_Kv.B = k_per_cm 1.38007535e-05 (v' = g - k|v|v, k = 0.00138 /m): with the 910 m/s muzzle speed drag adds exactly 1.00 m of drop at 500 m (vacuum drop 1.48 m -> 2.48 m,
    speed 456 m/s, 0.79 s). The tracer 'flown distance' constant (K2Node_FPB_Flown.B) was still the old 640 m/s -> 90000.
 3. Character BP: the bullet spawn point K2Node_FPF_Muzzle still had the AR15 muzzle (0, 40.625, 4.849) -> Colt muzzle from Data/colt_geometry.json; FPN_AimElev.B (50 m drop compensation angle, rad)
    -> 0.000307816 for the new k.   -> Data/bullet_visual.json"""
import unreal, json, os, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SC = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
K_CM = 1.38007535e-05; ELEV50 = 0.000307816; FLOWN = 90000.0
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); M = unreal.MaterialEditingLibrary
    G = json.load(open(os.path.join(D, 'colt_geometry.json')))
    p = '/Game/Furina/M4/M_BulletGlow'
    mat = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset('M_BulletGlow', '/Game/Furina/M4', unreal.Material, unreal.MaterialFactoryNew())
    assert mat, 'material'
    M.delete_all_material_expressions(mat); mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    c = M.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0); c.set_editor_property('constant', unreal.LinearColor(6.0, 4.2, 1.4, 1)); M.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat); R['mat_saved'] = E.save_loaded_asset(mat, False)
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    v = L.get_associated_object(L.get_data(hs['ProjectileVisual'])); v.set_material(0, mat); v.set_editor_property('relative_scale3d', unreal.Vector(SC, SC, SC)); v.set_editor_property('cast_shadow', False)
    R['visual_scale'] = SC
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    for name, pin, val in (('K2Node_FPB_Kv', 'B', repr(K_CM)), ('K2Node_FPB_Flown', 'B', repr(FLOWN))):
        pn = nodes[name].find_input_pin(pin); R.setdefault('before', {})[name] = pn.get_pin_value(); assert pn.set_pin_value(val); R.setdefault('after', {})[name] = pn.get_pin_value()
    del ed, nodes, v, hs
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['bullet_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['bullet_saved'] = E.save_loaded_asset(bp, False)
    del bp
    ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ch, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    muz = ','.join(repr(float(x)) for x in G['muzzle'])
    for name, pin, val in (('K2Node_FPF_Muzzle', 'Location', muz), ('FPN_AimElev', 'B', repr(ELEV50))):
        pn = nodes[name].find_input_pin(pin); R.setdefault('before', {})[name] = pn.get_pin_value(); assert pn.set_pin_value(val); R.setdefault('after', {})[name] = pn.get_pin_value()
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(ch); R['char_status'] = str(ch.get_editor_property('status'))
    if ch.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = E.save_loaded_asset(ch, False)
    del ch
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'bullet_visual.json'), 'w'), indent=1); print('BULLET_VISUAL', R.get('error', R.get('char_status'))[-300:])
