import unreal, json
R = {}
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
for h in S.k2_gather_subobject_data_for_blueprint(bp):
    o = L.get_associated_object(L.get_data(h)); n = str(L.get_variable_name(L.get_data(h)))
    if isinstance(o, unreal.PrimitiveComponent):
        R[n] = dict(cls=type(o).__name__, ce=str(o.get_collision_enabled()), obj=str(o.get_collision_object_type()), profile=str(o.get_collision_profile_name()),
                    resp={str(c).split('.')[-1]: str(o.get_collision_response_to_channel(c)).split('.')[-1] for c in (unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionChannel.ECC_PAWN, unreal.CollisionChannel.ECC_PHYSICS_BODY, unreal.CollisionChannel.ECC_VEHICLE, unreal.CollisionChannel.ECC_DESTRUCTIBLE)})
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_coll.json', 'w'), indent=1); print('BULLET_COLL', R)
