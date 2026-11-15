"""Dropped magazine fell through the floor (MagBody z went to -20000 in Data/drop_probe.json, so it vanished mid-air): the PhysicsBody object type / ignore-all profile did not
collide with the level floor. Now MagBody is a WorldDynamic physics body that blocks everything except Pawn (character capsule + mesh) and the visibility / camera traces,
with a little linear damping and 20 s life span."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    dbp = unreal.load_asset('/Game/Furina/M4/BP_M4MagDrop')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in S.k2_gather_subobject_data_for_blueprint(dbp):
        if str(L.get_variable_name(L.get_data(h))) == 'MagBody':
            b = L.get_associated_object(L.get_data(h))
            b.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS); b.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)
            b.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_BLOCK)
            for ch in (unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionChannel.ECC_CAMERA):
                b.set_collision_response_to_channel(ch, unreal.CollisionResponseType.ECR_IGNORE)
            b.set_simulate_physics(True); b.set_linear_damping(0.2); b.set_angular_damping(0.3)
            R['profile'] = str(b.get_collision_profile_name()); R['sim'] = bool(b.get_editor_property('body_instance').simulate_physics); del b
    unreal.BlueprintEditorLibrary.compile_blueprint(dbp)
    unreal.get_default_object(dbp.generated_class()).set_editor_property('initial_life_span', 20.0)
    R['status'] = str(dbp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(dbp, False); del dbp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\mag_drop_fix.json', 'w'), indent=1); print('MAG_DROP_FIX', R)
