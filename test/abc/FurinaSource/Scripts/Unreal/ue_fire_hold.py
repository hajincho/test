"""Fire-hold flag for the idle rest pose (2026-11-15):
 - character BP: float variable FurinaLastFire = game time of the last FurinaRifleShot event (the fire timer calls it for the first shot and for auto fire; set first, before any gate)
 - flag component FurinaFireHold (tag FurinaFireHold), set every 0.05 s (same view timer chain as FurinaSpecial / FurinaZip) to  (now - FurinaLastFire) < hold_seconds
 - ABP_Furina: curve 'FireHold' (ModifyCurve_ViewState names ViewTP, Crouch, Zip, FireHold)
CR_FurinaSecondary (ue_build_cr.py) leaves the rest pose for the normal third-person rifle pose while FireHold is up. usage: py ue_fire_hold.py [hold_seconds]"""
import unreal, json, traceback, sys
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
HOLD = sys.argv[1] if len(sys.argv) > 1 else '2.5'
def main():
    R = {}
    eal = unreal.EditorAssetLibrary
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaFireHold' not in handles():
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaFireHold')); R['comp'] = 'added'
    comp = lib.get_associated_object(lib.get_data(handles()['FurinaFireHold']))
    comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', ['FurinaFireHold']); del comp
    if 'FurinaLastFire' not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
        ok = False
        for tn in ('double', 'real', 'float'):
            try:
                t = unreal.BlueprintEditorLibrary.get_basic_type_by_name(tn)
                ok = unreal.BlueprintEditorLibrary.add_member_variable(bp, 'FurinaLastFire', t); R['var_type'] = tn
                if ok: break
            except Exception as e: R['var_err_' + tn] = str(e)[:100]
        R['var_added'] = ok
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    try: unreal.get_default_object(bp.generated_class()).set_editor_property('FurinaLastFire', -100.0); R['default'] = -100.0
    except Exception as e: R['default_err'] = str(e)[:100]
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    def call(name, path):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name); return n
    if 'FPN_FireLastSet' not in nodes:
        shot = nodes['K2Node_FPF_Shot']
        now = call('FPN_FireNow', '/Script/Engine.GameplayStatics:GetTimeSeconds')
        st = ed.add_set_member_variable_node('FurinaLastFire'); st.rename('FPN_FireLastSet'); R['set_pins'] = [str(p.get_pin_name()) for p in st.list_all_pins()]
        w(now.find_result_pin(), st.find_input_pin('FurinaLastFire'))
        old = list(shot.find_then_pin().list_connected_pins()); shot.find_then_pin().break_pin_links()
        w(shot.find_then_pin(), st.find_execute_pin())
        for p in old: w(st.find_then_pin(), p)
        R['shot_hooked'] = True
    if 'FPN_FireHoldSet' not in nodes:
        get = ed.add_get_member_variable_node('FurinaFireHold'); get.rename('FPN_FireHoldGet')
        setn = call('FPN_FireHoldSet', '/Script/Engine.ActorComponent:SetActive'); w(get.find_output_pin('FurinaFireHold'), setn.find_self_pin()); setn.find_input_pin('bReset').set_pin_value('false')
        now = call('FPN_FireNow2', '/Script/Engine.GameplayStatics:GetTimeSeconds')
        last = ed.add_get_member_variable_node('FurinaLastFire'); last.rename('FPN_FireLastGet')
        sub_ = call('FPN_FireSince', '/Script/Engine.KismetMathLibrary:Subtract_DoubleDouble'); R['sub_pins'] = [str(p.get_pin_name()) for p in sub_.list_all_pins()]
        w(now.find_result_pin(), sub_.find_input_pin('A')); w(last.find_output_pin('FurinaLastFire'), sub_.find_input_pin('B'))
        lt = call('FPN_FireLess', '/Script/Engine.KismetMathLibrary:Less_DoubleDouble')
        w(sub_.find_result_pin(), lt.find_input_pin('A')); lt.find_input_pin('B').set_pin_value(HOLD)
        w(lt.find_result_pin(), setn.find_input_pin('bNewActive'))
        zs = nodes['FPN_ZipSet']; old = list(zs.find_then_pin().list_connected_pins()); zs.find_then_pin().break_pin_links()
        w(zs.find_then_pin(), setn.find_execute_pin())
        for p in old: w(setn.find_then_pin(), p)
        R['flag'] = 'added'
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['char_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = eal.save_loaded_asset(bp, False)
    del bp
    # ---- ABP: curve FireHold
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph')
    n = next(n for n in unreal.AnimationLibrary.get_nodes_of_class(ab, unreal.AnimGraphNode_ModifyCurve, True) if n.get_name().endswith('ViewState'))
    v = n.get_editor_property('node'); text = v.export_text()
    if '"FireHold"' not in text:
        assert 'CurveNames=("ViewTP","Crouch","Zip")' in text, text[-300:]
        text = text.replace('CurveValues=(0.000000,0.000000,0.000000)', 'CurveValues=(0.000000,0.000000,0.000000,0.000000)').replace('CurveNames=("ViewTP","Crouch","Zip")', 'CurveNames=("ViewTP","Crouch","Zip","FireHold")')
        assert v.import_text(text); n.set_editor_property('node', v)
        old = n.get_editor_property('initial_update_function').copy(); tmp = old.copy()
        tmp.import_text('(MemberName="FurinaReconstructTemporary")'); n.set_editor_property('initial_update_function', tmp); n.set_editor_property('initial_update_function', old)
    R['pins'] = [str(p.get_pin_name()) for p in n.list_all_pins()]
    an = {x.get_name(): x for x in ed.list_all_nodes()}
    def acall(name, path):
        a = an.get(name)
        if not a: a = ed.add_call_function_node(path); assert a, path; a.rename(name); an[name] = a
        return a
    owner = an.get('TFPOwner') or an.get('FurinaCrouchOwner')
    find = acall('FurinaFireFind', '/Script/Engine.Actor:FindComponentByTag'); find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaFireHold')
    act = acall('FurinaFireActive', '/Script/Engine.ActorComponent:IsActive'); cv = acall('FurinaFireFloat', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble')
    for a, b in [(owner.find_result_pin(), find.find_self_pin()), (find.find_result_pin(), act.find_self_pin()), (act.find_result_pin(), cv.find_input_pin('InBool')), (cv.find_result_pin(), n.find_input_pin('CurveValues_3'))]:
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'abp link'
    del ed, n, v, an, owner, find, act, cv
    unreal.BlueprintEditorLibrary.compile_blueprint(ab); R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = eal.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\fire_hold.json', 'w'), indent=1); print('FIRE_HOLD', R.get('char_status'), R.get('abp_status'), R.get('error', '')[:300])
