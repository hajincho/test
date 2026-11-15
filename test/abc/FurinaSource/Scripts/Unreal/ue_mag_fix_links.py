"""Fix for ue_reload_mag.py: the 'set last state' node must be fed by the end of every state chain (my helper broke the earlier exec links);
and the dropped magazine only collides with the static world (it rested on the character's own physics bodies)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    setl = nodes['FMG_SetLast'].find_execute_pin()
    for tail in ('FMG_ShowHand', 'FMG_ShowHand2', 'FMG_HideMag', 'FMG_ShowSeated'):
        ok = unreal.BlueprintGraphPinLibrary.try_create_connection(nodes[tail].find_then_pin(), setl); R[tail] = ok
    R['setlast_inputs'] = [p.get_owning_node().get_name() for p in setl.list_connected_pins()]
    del ed, nodes, setl
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
    dbp = unreal.load_asset('/Game/Furina/M4/BP_M4MagDrop')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in S.k2_gather_subobject_data_for_blueprint(dbp):
        if str(L.get_variable_name(L.get_data(h))) == 'MagBody':
            b = L.get_associated_object(L.get_data(h))
            b.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS); b.set_collision_object_type(unreal.CollisionChannel.ECC_PHYSICS_BODY)
            b.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            b.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
            b.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)
            R['drop_profile'] = str(b.get_collision_profile_name()); del b
    unreal.BlueprintEditorLibrary.compile_blueprint(dbp); R['drop_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(dbp, False); del dbp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\mag_fix_links.json', 'w'), indent=1); print('MAG_FIX', R)
