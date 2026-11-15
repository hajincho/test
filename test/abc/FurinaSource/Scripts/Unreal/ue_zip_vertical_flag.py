"""Vertical / uphill ziplines (2026-11-15 b): the bundle rides those through Platformer_Component_BP (tag 'Vertical Zipline', variable 'Zipline Actor') and not always through the Grind component's UsingZipline?,
so the one-handed rappel pose never switched on there. FurinaZip and FurinaSpecial now also turn on while  IsValid(Platformer_Component_BP.'Zipline Actor') AND NOT IsMovingOnGround  (the ground
check keeps the flags from sticking if the variable is not cleared after a ride). Nodes FPN_ZipVert*. usage: py ue_zip_vertical_flag.py"""
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
    if 'FPN_ZipVertAnd' not in nodes:
        plat = ed.add_get_member_variable_node('Platformer_Component_BP'); plat.rename('FPN_ZipVertPlat'); R['plat_pins'] = [str(p.get_pin_name()) for p in plat.list_all_pins()]
        za = ed.add_get_member_variable_node('Zipline Actor', '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP.Platformer_Component_BP_C'); za.rename('FPN_ZipVertActor')
        w(plat.find_output_pin('Platformer_Component_BP'), za.find_self_pin())
        valid = call('FPN_ZipVertValid', '/Script/Engine.KismetSystemLibrary:IsValid'); w(za.find_output_pin('Zipline Actor'), valid.find_input_pin('Object'))
        an = call('FPN_ZipVertAnd', '/Script/Engine.KismetMathLibrary:BooleanAND'); w(valid.find_result_pin(), an.find_input_pin('A')); w(nodes['K2Node_FPV_NotGround'].find_result_pin(), an.find_input_pin('B'))
        for name, base_or, tgt_node, tgt_pin, src in (('FPN_ZipVertOrZip', None, 'FPN_ZipSet', 'bNewActive', 'K2Node_FPV_Flag1'), ('FPN_ZipVertOrSpecial', None, 'FPN_SpecialSet', 'bNewActive', 'K2Node_FPV_Or2')):
            o = call(name, '/Script/Engine.KismetMathLibrary:BooleanOR')
            if src == 'K2Node_FPV_Flag1': w(nodes[src].find_output_pin('UsingZipline?'), o.find_input_pin('A'))
            else: w(nodes[src].find_result_pin(), o.find_input_pin('A'))
            w(an.find_result_pin(), o.find_input_pin('B')); w(o.find_result_pin(), nodes[tgt_node].find_input_pin(tgt_pin))
        R['added'] = True
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\zip_vertical_flag.json', 'w'), indent=1); print('ZIP_VERT', R)
