"""No shooting during special moves (rail grind, zipline / rappel, rail jump) (2026-11-15). FurinaRifleShot (called by the fire timer, so it covers the
first shot and auto fire) now starts with a branch  NOT FurinaSpecial.IsActive  (the flag component set every 0.05 s by ue_special_motion.py);
when the flag is up the shot event does nothing (no ammo use, no auto-shoulder)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    R = {}
    bp = unreal.load_asset(CH)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    if 'FPN_SpecialFireGate' not in nodes:
        shot = nodes['K2Node_FPF_Shot']; sprint = nodes['K2Node_FPF_SprintB']
        get = ed.add_get_member_variable_node('FurinaSpecial'); get.rename('FPN_SpecialFireGet')
        act = ed.add_call_function_node('/Script/Engine.ActorComponent:IsActive'); act.rename('FPN_SpecialFireActive'); w(get.find_output_pin('FurinaSpecial'), act.find_self_pin())
        nt = ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Not_PreBool'); nt.rename('FPN_SpecialFireNot'); w(act.find_result_pin(), nt.find_input_pin('A'))
        gate = ed.add_branch_node(); gate.rename('FPN_SpecialFireGate'); w(nt.find_result_pin(), gate.find_input_pin('Condition'))
        shot.find_then_pin().break_pin_links()
        w(shot.find_then_pin(), gate.find_execute_pin()); w(gate.find_output_pin('then'), sprint.find_execute_pin())
        R['added'] = True
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\special_nofire.json', 'w'), indent=1); print('SPECIAL_NOFIRE', R)
