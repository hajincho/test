"""Prone locomotion from the 'Free Crawl Animation' pack (retargeted to /Game/Furina/Crawl) in ABP_Furina (2026-11-15):
 AnimGraph:  TwoWayBlend_1 (ground / crouch locomotion) --A--> ProneBlend --Pose--> LayeredBoneBlend_FP.BasePose
             ProneBlend.B = ProneMoveBlend (A = AS_Furina_Crawl_Prone_Idle, B = AS_Furina_Crawl_Move [in place, 61 cm/s], alpha TFPProneMove)
             ProneBlend.Alpha = TFPProne
 EventGraph: TFPProne = FInterpTo(TFPProne, FurinaProne flag, dt, PRONE_BLEND_SPEED);  TFPProneMove = MapRangeClamped(TFPSpeed, 5..30 -> 0..1)  (cached after CacheTFPHandIdle)
 usage: py ue_crawl_abp.py"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
BLEND_SPEED = '7'
def main():
    R = {}
    E = unreal.EditorAssetLibrary
    ab = unreal.load_asset('/Game/Furina/ABP_Furina')
    ev = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'EventGraph'); en = {n.get_name(): n for n in ev.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    names = [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(ab)]
    for v in ('TFPProne', 'TFPProneMove'):
        if v not in names: assert ev.add_member_variable(v, unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'), '0'), v
    def ecall(name, path):
        n = en.get(name)
        if not n: n = ev.add_call_function_node(path); assert n, path; n.rename(name); en[name] = n
        return n
    if 'CacheTFPProne' not in en:
        update = ev.find_event_node('BlueprintUpdateAnimation'); prev = en['CacheTFPHandIdle'].find_then_pin(); old = list(prev.list_connected_pins()); prev.break_pin_links()
        # TFPProne
        flag = ecall('TFPProneFlagF', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble'); w(en['ProneEvActive'].find_result_pin(), flag.find_input_pin('InBool'))
        cur = ev.add_get_member_variable_node('TFPProne'); sm = ecall('TFPProneSmooth', '/Script/Engine.KismetMathLibrary:FInterpTo')
        w(cur.find_output_pin('TFPProne'), sm.find_input_pin('Current')); w(flag.find_result_pin(), sm.find_input_pin('Target')); w(update.find_output_pin('DeltaTimeX'), sm.find_input_pin('DeltaTime')); sm.find_input_pin('InterpSpeed').set_pin_value(BLEND_SPEED)
        s1 = ev.add_set_member_variable_node('TFPProne'); s1.rename('CacheTFPProne'); en['CacheTFPProne'] = s1
        w(prev, s1.find_execute_pin()); w(sm.find_result_pin(), s1.find_input_pin('TFPProne'))
        # TFPProneMove
        spd = ev.add_get_member_variable_node('TFPSpeed'); mp = ecall('TFPProneMoveRange', '/Script/Engine.KismetMathLibrary:MapRangeClamped'); w(spd.find_output_pin('TFPSpeed'), mp.find_input_pin('Value'))
        for pin, val in (('InRangeA', 5), ('InRangeB', 30), ('OutRangeA', 0), ('OutRangeB', 1)): mp.find_input_pin(pin).set_pin_value(str(val))
        s2 = ev.add_set_member_variable_node('TFPProneMove'); s2.rename('CacheTFPProneMove'); en['CacheTFPProneMove'] = s2
        w(s1.find_then_pin(), s2.find_execute_pin()); w(mp.find_result_pin(), s2.find_input_pin('TFPProneMove'))
        for p in old: w(s2.find_then_pin(), p)
        R['event'] = 'added'
    del ev, en
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph'); an = {n.get_name(): n for n in ed.list_all_nodes()}
    def reconstruct(n):
        oldf = n.get_editor_property('initial_update_function').copy(); tmp = oldf.copy(); tmp.import_text('(MemberName="FurinaReconstructTemporary")'); n.set_editor_property('initial_update_function', tmp); n.set_editor_property('initial_update_function', oldf)
    def player(name, seq_path, x, y):
        n = an.get(name)
        if not n:
            n = ed.create_node_from_name('애니메이션|시퀀스|시퀀스플레이어', unreal.Vector2D(x, y), []); assert n, 'player'; n.rename(name); an[name] = n
        v = n.get_editor_property('node'); v.set_editor_property('sequence', unreal.load_asset(seq_path)); v.set_editor_property('loop_animation', True); n.set_editor_property('node', v)
        return n
    def blend(name, var, x, y):
        n = an.get(name)
        if not n:
            n = ed.create_node_from_name('애니메이션|블렌드|양방향블렌드', unreal.Vector2D(x, y), []); assert n, 'blend'; n.rename(name); an[name] = n
            v = n.get_editor_property('blend_node'); text = v.export_text().replace('AlphaInputType=Curve', 'AlphaInputType=Float').replace('AlphaInputType=Bool', 'AlphaInputType=Float'); assert v.import_text(text); n.set_editor_property('blend_node', v)
            opts = list(n.get_editor_property('show_pin_for_properties'))
            for i, o in enumerate(opts):
                if str(o.get_editor_property('PropertyName')) == 'Alpha': o.set_editor_property('bShowPin', True); opts[i] = o
            n.set_editor_property('show_pin_for_properties', opts); reconstruct(n)
            g = ed.add_get_member_variable_node(var); w(g.find_output_pin(var), n.find_input_pin('Alpha'))
        return n
    idle = player('ProneIdlePlayer', '/Game/Furina/Crawl/AS_Furina_Crawl_Prone_Idle', -1400, 1200)
    move = player('ProneMovePlayer', '/Game/Furina/Crawl/AS_Furina_Crawl_Move', -1400, 1400)
    mb = blend('ProneMoveBlend', 'TFPProneMove', -1100, 1300)
    pb = blend('ProneBlend', 'TFPProne', -800, 1200)
    R['pins'] = dict(idle=[str(p.get_pin_name()) for p in idle.list_all_pins()], blend=[str(p.get_pin_name()) for p in mb.list_all_pins()])
    w(idle.find_output_pin('Pose'), mb.find_input_pin('A')); w(move.find_output_pin('Pose'), mb.find_input_pin('B'))
    w(an['AnimGraphNode_TwoWayBlend_1'].find_output_pin('Pose'), pb.find_input_pin('A')); w(mb.find_output_pin('Pose'), pb.find_input_pin('B'))
    w(pb.find_output_pin('Pose'), an['AnimGraphNode_LayeredBoneBlend_FP'].find_input_pin('BasePose'))
    del ed, an
    unreal.BlueprintEditorLibrary.compile_blueprint(ab); R['abp_status'] = str(ab.get_editor_property('status'))
    if ab.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['abp_saved'] = E.save_loaded_asset(ab, False)
    del ab
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\crawl_abp.json', 'w'), indent=1); print('CRAWL_ABP', R.get('abp_status'), R.get('error', '')[-500:])
