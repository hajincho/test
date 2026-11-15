"""Restores the original special-move motions (rail grind, zipline / rappel, rail jump) for Furina (2026-11-15).
Cause: since the TFP locomotion, ABP_Furina blends the retargeted Manny pose (the bundle's own ABP: grind / zipline / jump poses) out as soon as
CharacterMovement.IsMovingOnGround is true - and on a rail or zipline it is. Fix:
 - character BP: flag component FurinaSpecial; the 0.05 s view timer (FurinaViewUpdate) sets it from  UsingRail? OR UsingZipline? OR RailJumpActive?
   (the same Or2 node that forces third person)
 - ABP_Furina EventGraph: TFPGround = IsMovingOnGround AND NOT FurinaSpecial.IsActive  -> the ground blend picks the retargeted Manny pose
   (TwoWayBlend_1 A) for every special move."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    R = {'log': []}
    eal = unreal.EditorAssetLibrary
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaSpecial' not in handles():
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaSpecial')); R['log'].append('added component')
    comp = lib.get_associated_object(lib.get_data(handles()['FurinaSpecial']))
    comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', ['FurinaSpecial']); del comp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    if 'FPN_SpecialSet' not in nodes:
        get = ed.add_get_member_variable_node('FurinaSpecial'); get.rename('FPN_SpecialGet')
        setn = ed.add_call_function_node('/Script/Engine.ActorComponent:SetActive'); setn.rename('FPN_SpecialSet')
        w(get.find_output_pin('FurinaSpecial'), setn.find_self_pin())
        w(nodes['K2Node_FPV_Or2'].find_result_pin(), setn.find_input_pin('bNewActive')); setn.find_input_pin('bReset').set_pin_value('false')
        upd = nodes['K2Node_FPV_Upd']; old = list(upd.find_then_pin().list_connected_pins())
        upd.find_then_pin().break_pin_links(); w(upd.find_then_pin(), setn.find_execute_pin())
        for p in old: w(setn.find_then_pin(), p)
        R['log'].append('special flag node')
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['char_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = eal.save_loaded_asset(bp, False)
    del bp
    # ---- ABP
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ae = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'EventGraph')
    an = {n.get_name(): n for n in ae.list_all_nodes()}
    if 'FurinaSpecialFind' not in an:
        ML = '/Script/Engine.KismetMathLibrary:'
        def fn(name, path):
            n = ae.add_call_function_node(path); assert n, path; n.rename(name); return n
        find = fn('FurinaSpecialFind', '/Script/Engine.Actor:FindComponentByTag')
        w(an['TFPOwner'].find_result_pin(), find.find_self_pin())
        find.find_input_pin('ComponentClass').set_pin_value('/Script/Engine.ActorComponent'); find.find_input_pin('Tag').set_pin_value('FurinaSpecial')
        act = fn('FurinaSpecialActive', '/Script/Engine.ActorComponent:IsActive'); w(find.find_result_pin(), act.find_self_pin())
        nots = fn('FurinaNotSpecial', ML + 'Not_PreBool'); w(act.find_result_pin(), nots.find_input_pin('A'))
        andn = fn('FurinaGroundAnd', ML + 'BooleanAND')
        w(an['TFPOnGround'].find_result_pin(), andn.find_input_pin('A')); w(nots.find_result_pin(), andn.find_input_pin('B'))
        w(andn.find_result_pin(), an['TFPGroundFloat'].find_input_pin('InBool'))
        R['log'].append('abp ground gate')
    del ae, an
    unreal.BlueprintEditorLibrary.compile_blueprint(ab)
    R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = eal.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\special_motion.json', 'w'), indent=1)
print('SPECIAL_MOTION', R.get('char_status'), R.get('abp_status'), R.get('error', '')[:300])
