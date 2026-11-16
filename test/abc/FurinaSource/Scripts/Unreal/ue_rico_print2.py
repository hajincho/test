"""Extends the ricochet debug print FRC_PrintHit with ' loc=<HitLocation> v=<velocity>' (PIE stopped) -> Data/rico_print2.json"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def link(a, b): assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    def mk(name, path):
        n = nodes.get(name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; R.setdefault('added', []).append(name)
        return n
    KS = '/Script/Engine.KismetStringLibrary:'
    if 'FRC_Cat7' not in nodes:
        hl = mk('FRC_StrLoc', KS + 'Conv_VectorToString'); link(nodes['K2Node_FPB_Hit'].find_output_pin('HitLocation'), hl.find_input_pin('InVec'))
        vl = mk('FRC_StrVel', KS + 'Conv_VectorToString'); link(nodes['K2Node_FPB_Vel2'].find_output_pin('Velocity'), vl.find_input_pin('InVec'))
        c4 = mk('FRC_Cat4', KS + 'Concat_StrStr'); link(nodes['FRC_Cat3'].find_result_pin(), c4.find_input_pin('A')); c4.find_input_pin('B').set_pin_value(' loc=')
        c5 = mk('FRC_Cat5', KS + 'Concat_StrStr'); link(c4.find_result_pin(), c5.find_input_pin('A')); link(hl.find_result_pin(), c5.find_input_pin('B'))
        c6 = mk('FRC_Cat6', KS + 'Concat_StrStr'); link(c5.find_result_pin(), c6.find_input_pin('A')); c6.find_input_pin('B').set_pin_value(' v=')
        c7 = mk('FRC_Cat7', KS + 'Concat_StrStr'); link(c6.find_result_pin(), c7.find_input_pin('A')); link(vl.find_result_pin(), c7.find_input_pin('B'))
        link(c7.find_result_pin(), nodes['FRC_PrintHit'].find_input_pin('InString'))
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'rico_print2.json'), 'w'), indent=1); print('RICO_PRINT2', R.get('error', R.get('status'))[-300:])
