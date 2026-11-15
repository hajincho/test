"""Fix (2026-11-15): pressing V while aiming down the sights (ADS) toggled FurinaFPWanted off, so the view dropped to third person in the middle of ADS (ADS forces first person through FurinaFPWanted).
Now V (IA_FurinaViewToggle, K2Node_FPV_ViewIA.Started) is a branch on FurinaADS.IsActive:
   ADS active   -> ToggleActive(FurinaADSRestoreTP): V chooses the view you get back after leaving ADS (restore flag on = back to third person, off = stay first person); the view stays first person during ADS
   ADS inactive -> the old ToggleActive(FurinaFPWanted)
Nodes FPN_ViewAds*. usage: py ue_view_ads_fix.py"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def main():
    R = {}
    bp = unreal.load_asset(CH); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    def call(name, path):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; return n
    if 'FPN_ViewAdsBranch' not in nodes:
        ia = nodes['K2Node_FPV_ViewIA']; old = nodes['K2Node_FPV_Toggle']
        ads = ed.add_get_member_variable_node('FurinaADS'); ads.rename('FPN_ViewAdsGet')
        act = call('FPN_ViewAdsActive', '/Script/Engine.ActorComponent:IsActive'); w(ads.find_output_pin('FurinaADS'), act.find_self_pin())
        br = ed.add_branch_node(); br.rename('FPN_ViewAdsBranch'); w(act.find_result_pin(), br.find_input_pin('Condition'))
        rest = ed.add_get_member_variable_node('FurinaADSRestoreTP'); rest.rename('FPN_ViewAdsRestoreGet')
        tg = call('FPN_ViewAdsToggleRestore', '/Script/Engine.ActorComponent:ToggleActive'); w(rest.find_output_pin('FurinaADSRestoreTP'), tg.find_self_pin())
        ia.find_output_pin('Started').break_pin_links()
        w(ia.find_output_pin('Started'), br.find_execute_pin()); w(br.find_output_pin('then'), tg.find_execute_pin()); w(br.find_output_pin('else'), old.find_execute_pin())
        R['added'] = True
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\view_ads_fix.json', 'w'), indent=1); print('VIEW_ADS_FIX', R)
