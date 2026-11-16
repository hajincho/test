"""Reads BP_FurinaBullet: component transforms / materials, projectile movement settings, mesh bounds of SM_223Projectile; character BP lift nodes (K2Node_FPF_Lift, LiftM, Far) -> Data/bullet_probe2.json"""
import unreal, json
R = {}
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
for h in S.k2_gather_subobject_data_for_blueprint(bp):
    o = L.get_associated_object(L.get_data(h)); n = str(L.get_variable_name(L.get_data(h))); e = {'class': o.get_class().get_name()}
    if isinstance(o, unreal.PrimitiveComponent) or isinstance(o, unreal.SceneComponent):
        for a in ('relative_location', 'relative_rotation', 'relative_scale3d'):
            try: e[a] = str(o.get_editor_property(a))
            except Exception: pass
    if isinstance(o, unreal.StaticMeshComponent): e.update(mesh=str(o.static_mesh.get_name()) if o.static_mesh else None, mat=[str(m.get_path_name()) for m in o.get_materials()])
    if isinstance(o, unreal.SphereComponent): e['radius'] = o.get_editor_property('sphere_radius')
    if isinstance(o, unreal.ProjectileMovementComponent):
        for a in ('initial_speed', 'max_speed', 'projectile_gravity_scale', 'rotation_follows_velocity', 'bounce'):
            try: e[a] = str(o.get_editor_property(a))
            except Exception as ex: e[a] = 'ERR'
    R[n] = e
m = unreal.load_asset('/Game/Furina/M4/SM_223Projectile'); b = m.get_bounds(); R['SM_223Projectile'] = dict(origin=str(b.origin), extent=str(b.box_extent))
c = unreal.load_asset('/Game/Furina/M4/SM_223Case'); b = c.get_bounds(); R['SM_223Case'] = dict(origin=str(b.origin), extent=str(b.box_extent))
ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ch, 'EventGraph')
for n in ed.list_all_nodes():
    nm = n.get_name()
    if nm.startswith('K2Node_FPF_') and any(k in nm for k in ('Lift', 'Far', 'Zero', 'Muz', 'Spd', 'Speed', 'Spawn')):
        R['char.' + nm] = [[str(p.get_pin_name()), p.get_pin_value()] for p in n.list_all_pins() if p.get_pin_value() not in ('', None)][:10]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_probe2.json', 'w'), indent=1); print('BULLET_PROBE2'); del ed, ch
