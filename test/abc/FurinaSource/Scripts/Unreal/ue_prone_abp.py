"""Prone stance, animation side (2026-11-15):
 - ABP_Furina EventGraph: the crouch input of the locomotion blend (TFPCrouchFloat <- TFPIsCrouched) becomes  IsCrouching AND NOT FurinaProne.IsActive, so a prone character keeps the standing
   blend space (straight legs) - the Control Rig then lies the whole body down
 - ABP_Furina AnimGraph: ModifyCurve_ViewState gets the curve 'Prone' (names ViewTP, Crouch, Zip, FireHold, Prone) = FurinaProne.IsActive"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    E = unreal.EditorAssetLibrary
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ev = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'EventGraph'); en = {n.get_name(): n for n in ev.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    def ecall(name, path):
        n = en.get(name)
        if not n: n = ev.add_call_function_node(path); assert n, path; n.rename(name); en[name] = n
        return n
    if 'ProneNotAnd' not in en:
        find = ecall('ProneEvFind', '/Script/Engine.Actor:FindComponentByTag'); find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaProne')
        act = ecall('ProneEvActive', '/Script/Engine.ActorComponent:IsActive'); nt = ecall('ProneEvNot', '/Script/Engine.KismetMathLibrary:Not_PreBool'); an = ecall('ProneNotAnd', '/Script/Engine.KismetMathLibrary:BooleanAND')
        w(en['TFPOwner'].find_result_pin(), find.find_self_pin()); w(find.find_result_pin(), act.find_self_pin()); w(act.find_result_pin(), nt.find_input_pin('A'))
        w(en['TFPIsCrouched'].find_result_pin(), an.find_input_pin('A')); w(nt.find_result_pin(), an.find_input_pin('B')); w(an.find_result_pin(), en['TFPCrouchFloat'].find_input_pin('InBool'))
        R['event'] = 'added'
    del ev, en
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph')
    n = next(n for n in unreal.AnimationLibrary.get_nodes_of_class(ab, unreal.AnimGraphNode_ModifyCurve, True) if n.get_name().endswith('ViewState'))
    v = n.get_editor_property('node'); text = v.export_text()
    if '"Prone"' not in text:
        assert 'CurveNames=("ViewTP","Crouch","Zip","FireHold")' in text, text[-300:]
        text = text.replace('CurveValues=(0.000000,0.000000,0.000000,0.000000)', 'CurveValues=(0.000000,0.000000,0.000000,0.000000,0.000000)').replace('CurveNames=("ViewTP","Crouch","Zip","FireHold")', 'CurveNames=("ViewTP","Crouch","Zip","FireHold","Prone")')
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
    find = acall('FurinaProneFind', '/Script/Engine.Actor:FindComponentByTag'); find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaProne')
    act = acall('FurinaProneActive', '/Script/Engine.ActorComponent:IsActive'); cv = acall('FurinaProneFloat', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble')
    for a, b in [(owner.find_result_pin(), find.find_self_pin()), (find.find_result_pin(), act.find_self_pin()), (act.find_result_pin(), cv.find_input_pin('InBool')), (cv.find_result_pin(), n.find_input_pin('CurveValues_4'))]:
        assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'abp link'
    del ed, n, v, an, owner, find, act, cv
    unreal.BlueprintEditorLibrary.compile_blueprint(ab); R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = E.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\prone_abp.json', 'w'), indent=1); print('PRONE_ABP', R.get('abp_status'), R.get('error', '')[-400:])
