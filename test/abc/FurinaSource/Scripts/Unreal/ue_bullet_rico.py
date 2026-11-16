"""Brass bullet + ricochet (2026-11-16). PIE stopped.
 1. Colour: M_BulletGlow (bullet head) emissive brass (0.55, 0.45, 0.12); the tracer streak M_FurinaTracer brass-gold (0.30, 0.25, 0.07) instead of the saturated orange.
 2. Ricochet in BP_FurinaBullet: on a blocking hit the angle between the flight direction and the SURFACE is asin(|v_hat . HitNormal|); when it is below 20 deg (|dot| < sin 20 = 0.34202) and a random 0..1 is
    below 0.4 and the bullet has not ricocheted before (variable FurinaRico == 0) the bullet is not destroyed: FurinaRico = 1, a Niagara spark (Sparks_FXS, scale 0.1) is spawned at the hit point and the
    built-in ProjectileMovement bounce reflects it (bShouldBounce, Bounciness 0.5, Friction 0.3 -> it keeps about half of its normal speed and loses some tangential speed). Every other hit runs the old
    path (debug sphere, impulse on physics bodies, destroy). Nodes FRC_*.     -> Data/bullet_rico.json"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    E = unreal.EditorAssetLibrary; M = unreal.MaterialEditingLibrary
    # colours
    for path, col in (('/Game/Furina/M4/M_BulletGlow', (0.55, 0.45, 0.12)), ('/Game/Furina/FP/Weapon/M_FurinaTracer', (0.30, 0.25, 0.07))):
        mat = unreal.load_asset(path)
        for ex in M.get_material_expressions(mat) if hasattr(M, 'get_material_expressions') else []: pass
        M.delete_all_material_expressions(mat); mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
        c = M.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0); c.set_editor_property('constant', unreal.LinearColor(*col, 1)); M.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        M.recompile_material(mat); R[path] = E.save_loaded_asset(mat, False)
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FurinaRico' not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
        ed.add_member_variable('FurinaRico', unreal.BlueprintEditorLibrary.get_basic_type_by_name('int'), '0')
    def link(a, b): assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    ML = '/Script/Engine.KismetMathLibrary:'
    def mk(name, path):
        n = nodes.get(name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n
        return n
    if 'FRC_Branch' not in nodes:
        hit = nodes['K2Node_FPB_Hit']; mark = nodes['K2Node_FPB_Mark']
        dot = mk('FRC_Dot', ML + 'Dot_VectorVector'); link(nodes['K2Node_FPB_Dir'].find_result_pin(), dot.find_input_pin('A')); link(hit.find_output_pin('HitNormal'), dot.find_input_pin('B'))
        ab = mk('FRC_Abs', ML + 'Abs'); link(dot.find_result_pin(), ab.find_input_pin('A'))
        gz = mk('FRC_Grazing', ML + 'Less_DoubleDouble'); link(ab.find_result_pin(), gz.find_input_pin('A')); gz.find_input_pin('B').set_pin_value('0.34202')
        rn = mk('FRC_Random', ML + 'RandomFloat')
        pr = mk('FRC_Prob', ML + 'Less_DoubleDouble'); link(rn.find_result_pin(), pr.find_input_pin('A')); pr.find_input_pin('B').set_pin_value('0.4')
        cnt = nodes.get('FRC_GetCount')
        if cnt is None: cnt = ed.add_get_member_variable_node('FurinaRico'); cnt.rename('FRC_GetCount'); nodes['FRC_GetCount'] = cnt
        zero = mk('FRC_FirstTime', ML + 'EqualEqual_IntInt'); link(cnt.find_output_pin('FurinaRico'), zero.find_input_pin('A')); zero.find_input_pin('B').set_pin_value('0')
        a1 = mk('FRC_And1', ML + 'BooleanAND'); link(gz.find_result_pin(), a1.find_input_pin('A')); link(pr.find_result_pin(), a1.find_input_pin('B'))
        a2 = mk('FRC_And2', ML + 'BooleanAND'); link(a1.find_result_pin(), a2.find_input_pin('A')); link(zero.find_result_pin(), a2.find_input_pin('B'))
        br = ed.add_branch_node(); br.rename('FRC_Branch'); nodes['FRC_Branch'] = br; link(a2.find_result_pin(), br.find_input_pin('Condition'))
        sc = ed.add_set_member_variable_node('FurinaRico'); sc.rename('FRC_SetCount'); nodes['FRC_SetCount'] = sc; sc.find_input_pin('FurinaRico').set_pin_value('1')
        sp = mk('FRC_Spark', '/Script/Niagara.NiagaraFunctionLibrary:SpawnSystemAtLocation'); assert sp.find_input_pin('SystemTemplate').set_pin_value('/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS.Sparks_FXS'); sp.find_input_pin('Scale').set_pin_value('0.1,0.1,0.1')
        link(hit.find_output_pin('HitLocation'), sp.find_input_pin('Location'))
        # Hit.then -> branch ; true -> SetCount -> Spark ; false -> old chain (DrawDebugSphere ...)
        hit.find_then_pin().break_pin_links()
        link(hit.find_then_pin(), br.find_execute_pin()); link(br.find_output_pin('then'), sc.find_execute_pin()); link(sc.find_then_pin(), sp.find_execute_pin()); link(br.find_output_pin('else'), mark.find_execute_pin())
        R['added'] = True
    del ed, nodes
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    pm = L.get_associated_object(L.get_data(hs['Ballistics']))
    pm.set_editor_property('should_bounce', True); pm.set_editor_property('bounciness', 0.5); pm.set_editor_property('friction', 0.3)
    R['bounce'] = [pm.get_editor_property('should_bounce'), pm.get_editor_property('bounciness'), pm.get_editor_property('friction')]
    del pm, hs
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'bullet_rico.json'), 'w'), indent=1); print('BULLET_RICO', R.get('error', R.get('status'))[-300:])
