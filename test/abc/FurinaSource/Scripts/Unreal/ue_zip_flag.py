"""Zipline / rappel state for the Control Rig (2026-11-15):
 - character BP: flag component FurinaZip (tag FurinaZip), set every 0.05 s from the Grind component's UsingZipline? (the same view timer that sets FurinaSpecial)
 - ABP_Furina: curve 'Zip' (0/1) added to ModifyCurve_ViewState (names ViewTP, Crouch, Zip), value = FurinaZip.IsActive
The Control Rig (ue_build_cr.py, zip_* nodes) uses it: left hand keeps the bundle's one-handed zipline pose, right hand carries the rifle one-handed."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    R = {}
    eal = unreal.EditorAssetLibrary
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaZip' not in handles():
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaZip')); R['comp'] = 'added'
    comp = lib.get_associated_object(lib.get_data(handles()['FurinaZip']))
    comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', ['FurinaZip']); del comp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    if 'FPN_ZipSet' not in nodes:
        get = ed.add_get_member_variable_node('FurinaZip'); get.rename('FPN_ZipGet')
        setn = ed.add_call_function_node('/Script/Engine.ActorComponent:SetActive'); setn.rename('FPN_ZipSet')
        w(get.find_output_pin('FurinaZip'), setn.find_self_pin())
        w(nodes['K2Node_FPV_Flag1'].find_output_pin('UsingZipline?'), setn.find_input_pin('bNewActive')); setn.find_input_pin('bReset').set_pin_value('false')
        sp = nodes['FPN_SpecialSet']; old = list(sp.find_then_pin().list_connected_pins())
        sp.find_then_pin().break_pin_links(); w(sp.find_then_pin(), setn.find_execute_pin())
        for p in old: w(setn.find_then_pin(), p)
        R['flag'] = 'added'
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['char_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = eal.save_loaded_asset(bp, False)
    del bp
    # ---- ABP
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph')
    n = next(n for n in unreal.AnimationLibrary.get_nodes_of_class(ab, unreal.AnimGraphNode_ModifyCurve, True) if n.get_name().endswith('ViewState'))
    v = n.get_editor_property('node'); text = v.export_text(); R['text_before'] = text[-300:]
    if '"Zip"' not in text:
        assert 'CurveNames=("ViewTP","Crouch")' in text, text[-300:]
        text = text.replace('CurveValues=(0.000000,0.000000)', 'CurveValues=(0.000000,0.000000,0.000000)').replace('CurveNames=("ViewTP","Crouch")', 'CurveNames=("ViewTP","Crouch","Zip")')
        assert v.import_text(text); n.set_editor_property('node', v)
        old = n.get_editor_property('initial_update_function').copy(); tmp = old.copy()
        tmp.import_text('(MemberName="FurinaReconstructTemporary")'); n.set_editor_property('initial_update_function', tmp); n.set_editor_property('initial_update_function', old)
    R['pins'] = [str(p.get_pin_name()) for p in n.list_all_pins()]
    an = {x.get_name(): x for x in ed.list_all_nodes()}
    def call(name, path):
        a = an.get(name)
        if not a: a = ed.add_call_function_node(path); assert a, path; a.rename(name); an[name] = a
        return a
    owner = an.get('TFPOwner') or an.get('FurinaCrouchOwner')
    find = call('FurinaZipFind', '/Script/Engine.Actor:FindComponentByTag'); find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaZip')
    act = call('FurinaZipActive', '/Script/Engine.ActorComponent:IsActive'); cv = call('FurinaZipFloat', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble')
    for a, b in [(owner.find_result_pin(), find.find_self_pin()), (find.find_result_pin(), act.find_self_pin()), (act.find_result_pin(), cv.find_input_pin('InBool')), (cv.find_result_pin(), n.find_input_pin('CurveValues_2'))]:
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'abp link'
    del ed, n, v, an, owner, find, act, cv
    unreal.BlueprintEditorLibrary.compile_blueprint(ab); R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = eal.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\zip_flag.json', 'w'), indent=1); print('ZIP_FLAG', R.get('char_status'), R.get('abp_status'), R.get('error', '')[:300])
