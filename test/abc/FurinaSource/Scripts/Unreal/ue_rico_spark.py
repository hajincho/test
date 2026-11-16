"""Ricochet spark lifetime (2026-11-16): the Niagara spark spawned by SpawnSystemAtLocation (FRC_Spark in BP_FurinaBullet) lasted as long as the system wants. Now a tiny actor BP_RicoSpark
(Niagara component with /Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS, relative scale 0.1, InitialLifeSpan 0.1 s) is spawned at the hit point, so the actor and its particles disappear after 0.1 s
even if the bullet is destroyed by the next hit. Bullet chain: FRC_PrintTrue.then -> FRC_RSpawn (BeginDeferredActorSpawnFromClass) -> FRC_RFinish; the old FRC_Spark node stays in the graph, disconnected.
usage: py ue_rico_spark.py [life_seconds]  (PIE stopped) -> Data/rico_spark.json"""
import unreal, json, os, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; DEST = '/Game/Furina/M4'
LIFE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    p = DEST + '/BP_RicoSpark'
    if E.does_asset_exist(p): bp = unreal.load_asset(p)
    else: f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); bp = T.create_asset('BP_RicoSpark', DEST, unreal.Blueprint, f)
    assert bp, 'bp'
    hs = {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    if 'Sparks' not in hs:
        h, err = S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs.get('DefaultSceneRoot', next(iter(hs.values()))), new_class=unreal.NiagaraComponent, blueprint_context=bp)); assert not str(err), str(err); S.rename_subobject(h, unreal.Text('Sparks')); hs['Sparks'] = h
    c = L.get_associated_object(L.get_data(hs['Sparks']))
    c.set_asset(unreal.load_asset('/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS')); c.set_editor_property('auto_activate', True); c.set_editor_property('relative_scale3d', unreal.Vector(0.1, 0.1, 0.1))
    del c, hs
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    unreal.get_default_object(bp.generated_class()).set_editor_property('initial_life_span', LIFE); R['spark_saved'] = E.save_loaded_asset(bp, False); R['life'] = unreal.get_default_object(bp.generated_class()).get_editor_property('initial_life_span')
    del bp
    bb = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bb, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def link(a, b): assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    def mk(name, path):
        n = nodes.get(name)
        if n is None: n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; R.setdefault('added', []).append(name)
        return n
    if 'FRC_RSpawn' not in nodes:
        xf = mk('FRC_RXf', '/Script/Engine.KismetMathLibrary:MakeTransform'); link(nodes['K2Node_FPB_Hit'].find_output_pin('HitLocation'), xf.find_input_pin('Location')); xf.find_input_pin('Scale').set_pin_value('1,1,1')
        sp = mk('FRC_RSpawn', '/Script/Engine.GameplayStatics:BeginDeferredActorSpawnFromClass'); assert sp.find_input_pin('ActorClass').set_pin_value(DEST + '/BP_RicoSpark.BP_RicoSpark_C'); link(xf.find_result_pin(), sp.find_input_pin('SpawnTransform')); sp.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn')
        fin = mk('FRC_RFinish', '/Script/Engine.GameplayStatics:FinishSpawningActor'); link(sp.find_result_pin(), fin.find_input_pin('Actor')); link(xf.find_result_pin(), fin.find_input_pin('SpawnTransform'))
        link(sp.find_then_pin(), fin.find_execute_pin())
        pt = nodes['FRC_PrintTrue']; pt.find_then_pin().break_pin_links(); link(pt.find_then_pin(), sp.find_execute_pin())
        R['rewired'] = True
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bb); R['bullet_status'] = str(bb.get_editor_property('status'))
    if bb.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['bullet_saved'] = E.save_loaded_asset(bb, False)
    del bb
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'rico_spark.json'), 'w'), indent=1); print('RICO_SPARK', R.get('error', R.get('bullet_status'))[-300:])
