"""Debug prints for the ricochet branch (BP_FurinaBullet): FRC_PrintHit (Hit.then -> print -> FRC_Branch) logs 'RICO hit dot=<|v.n|> count=<FurinaRico>' and FRC_PrintTrue logs 'RICO TRUE' in the ricochet path.
usage: py ue_rico_print.py <1|0>   (1 = logging on, 0 = off: bPrintToLog false)   -> Data/rico_print.json ; PIE stopped"""
import unreal, json, os, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
ON = (sys.argv[1] if len(sys.argv) > 1 else '1') == '1'
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def link(a, b): assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    def mk(name, path):
        n = nodes.get(name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; R.setdefault('added', []).append(name)
        return n
    KS = '/Script/Engine.KismetStringLibrary:'; KY = '/Script/Engine.KismetSystemLibrary:'
    p1 = mk('FRC_PrintHit', KY + 'PrintString'); p2 = mk('FRC_PrintTrue', KY + 'PrintString')
    if 'FRC_PrintHit' in R.get('added', []):
        c1 = mk('FRC_StrDot', KS + 'Conv_DoubleToString'); link(nodes['FRC_Abs'].find_result_pin(), c1.find_input_pin('InDouble'))
        c2 = mk('FRC_StrCnt', KS + 'Conv_IntToString'); link(nodes['FRC_GetCount'].find_output_pin('FurinaRico'), c2.find_input_pin('InInt'))
        a = mk('FRC_Cat1', KS + 'Concat_StrStr'); a.find_input_pin('A').set_pin_value('RICO hit dot='); link(c1.find_result_pin(), a.find_input_pin('B'))
        b = mk('FRC_Cat2', KS + 'Concat_StrStr'); link(a.find_result_pin(), b.find_input_pin('A')); b.find_input_pin('B').set_pin_value(' count=')
        c = mk('FRC_Cat3', KS + 'Concat_StrStr'); link(b.find_result_pin(), c.find_input_pin('A')); link(c2.find_result_pin(), c.find_input_pin('B'))
        link(c.find_result_pin(), p1.find_input_pin('InString')); p2.find_input_pin('InString').set_pin_value('RICO TRUE')
        hit = nodes['K2Node_FPB_Hit']; br = nodes['FRC_Branch']; sc = nodes['FRC_SetCount']
        hit.find_then_pin().break_pin_links(); link(hit.find_then_pin(), p1.find_execute_pin()); link(p1.find_then_pin(), br.find_execute_pin())
        sc.find_then_pin().break_pin_links(); nxt = nodes['FRC_Spark'].find_execute_pin(); link(sc.find_then_pin(), p2.find_execute_pin()); link(p2.find_then_pin(), nxt)
    for p in (p1, p2):
        p.find_input_pin('bPrintToScreen').set_pin_value('false'); p.find_input_pin('bPrintToLog').set_pin_value('true' if ON else 'false')
    R['log_on'] = ON
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'rico_print.json'), 'w'), indent=1); print('RICO_PRINT', R.get('error', R.get('status'))[-300:])
