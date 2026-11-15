"""Bullets must not hit / stick in the dropped magazine (2026-11-15): BP_FurinaBullet's sphere (WorldDynamic, BlockAllDynamic) blocked every physics body, so projectiles stopped at
a dropped magazine lying near the player. Now the bullet ignores the PhysicsBody channel and the dropped magazine is a PhysicsBody object (blocks the floor and other statics,
ignores Pawn / visibility / camera). Also: BP_223Case keeps working the same way (PhysicsBody)."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}; E = unreal.EditorAssetLibrary
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    def comp(bp, name):
        for h in S.k2_gather_subobject_data_for_blueprint(bp):
            if str(L.get_variable_name(L.get_data(h))) == name: return L.get_associated_object(L.get_data(h))
    dbp = unreal.load_asset('/Game/Furina/M4/BP_M4MagDrop'); b = comp(dbp, 'MagBody')
    b.set_collision_object_type(unreal.CollisionChannel.ECC_PHYSICS_BODY); b.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_BLOCK)
    for ch in (unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionChannel.ECC_CAMERA, unreal.CollisionChannel.ECC_WORLD_DYNAMIC):
        b.set_collision_response_to_channel(ch, unreal.CollisionResponseType.ECR_IGNORE)
    del b; unreal.BlueprintEditorLibrary.compile_blueprint(dbp); R['drop'] = [str(dbp.get_editor_property('status')), E.save_loaded_asset(dbp, False)]; del dbp
    bbp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); s = comp(bbp, 'Bullet')
    s.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PHYSICS_BODY, unreal.CollisionResponseType.ECR_IGNORE); del s
    unreal.BlueprintEditorLibrary.compile_blueprint(bbp); R['bullet'] = [str(bbp.get_editor_property('status')), E.save_loaded_asset(bbp, False)]; del bbp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\mag_drop_fix2.json', 'w'), indent=1); print('MAG_DROP_FIX2', R)
