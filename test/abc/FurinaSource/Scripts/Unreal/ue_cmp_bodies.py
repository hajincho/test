import unreal, json
R = {}
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
for p in ('BP_223Case', 'BP_M4MagDrop'):
    bp = unreal.load_asset('/Game/Furina/M4/' + p); R[p] = {}
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h)); n = str(L.get_variable_name(L.get_data(h)))
        if isinstance(o, unreal.StaticMeshComponent):
            bi = o.get_editor_property('body_instance')
            R[p][n] = dict(mesh=o.static_mesh.get_name() if o.static_mesh else None, ce=str(o.get_collision_enabled()), obj=str(o.get_collision_object_type()), sim=bool(bi.simulate_physics), grav=bool(bi.enable_gravity),
                           profile=str(o.get_collision_profile_name()), ws=str(o.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC)), mass=str(bi.get_editor_property('mass_in_kg_override')) if hasattr(bi, 'get_editor_property') else None,
                           scale=str(o.get_editor_property('relative_scale3d')), parent=str(L.get_variable_name(L.get_data(S.k2_find_parent_subobject(h)))) if False else None)
        else: R[p][n] = type(o).__name__
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\cmp_bodies.json', 'w'), indent=1, default=str); print('CMP', R)
