"""Tracer rounds with bullet drop (numbers: Data/ballistics.json from Tools/gen_ballistics.py).
 - M_FurinaTracer: unlit, saturated orange emissive (8, 1.4, 0.08): brighter values tonemap to white
 - BP_FurinaBullet (Actor): Bullet (Sphere r=1.5, root, BlockAllDynamic) > Tracer (Cylinder, grows behind the round from the
   muzzle up to 6 m) + Ballistics (ProjectileMovement: 640 m/s, gravity 1, rotation follows velocity, no bounce).
   Air drag, hit impulse, despawn: graph text from Tools/gen_fp_bullet_t3d.py. InitialLifeSpan 4 s.
 - IA_FurinaFireAuto on LeftMouseButton (full auto, 800 rpm timer); IA_FurinaFire (single shot) unmapped from LMB."""
import unreal, json
DATA = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    B = json.load(open(DATA + r'\ballistics.json'))
    R = {'log': []}
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools(); mel = unreal.MaterialEditingLibrary
    # ---- material
    mp = '/Game/Furina/FP/Weapon/M_FurinaTracer'
    if eal.does_asset_exist(mp): mat = unreal.load_asset(mp); mel.delete_all_material_expressions(mat)
    else: mat = tools.create_asset('M_FurinaTracer', '/Game/Furina/FP/Weapon', unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property('constant', unreal.LinearColor(8.0, 1.4, 0.08, 1.0))
    mel.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat); eal.save_loaded_asset(mat, False); del c
    # ---- bullet actor
    bp_path = '/Game/Furina/FP/BP_FurinaBullet'
    if eal.does_asset_exist(bp_path): bp = unreal.load_asset(bp_path)
    else:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = tools.create_asset('BP_FurinaBullet', '/Game/Furina/FP', None, f); R['log'].append('created bp')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def obj(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    hs = handles(); R['before'] = list(hs)
    root = [h for n, h in hs.items() if lib.is_root_component(lib.get_data(h))]
    if 'Bullet' not in hs:
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root[0] if root else hs[list(hs)[0]], new_class=unreal.SphereComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('Bullet'))
        hs = handles()
        try:
            R['make_root'] = str(sub.make_new_scene_root(hs[list(hs)[0]], hs['Bullet'], bp))
        except Exception as e:
            R['make_root_err'] = str(e)
    hs = handles()
    if 'Tracer' not in hs:
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['Bullet'], new_class=unreal.StaticMeshComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('Tracer'))
    hs = handles()
    if 'Ballistics' not in hs:
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[list(hs)[0]], new_class=unreal.ProjectileMovementComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('Ballistics'))
    hs = handles()
    R['after'] = list(hs); R['roots'] = [n for n, h in hs.items() if lib.is_root_component(lib.get_data(h))]
    s = obj('Bullet')
    s.set_editor_property('sphere_radius', 1.5)
    s.set_collision_profile_name('BlockAllDynamic')
    s.set_editor_property('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)
    t = obj('Tracer')
    t.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    t.set_material(0, mat)
    t.set_collision_profile_name('NoCollision')
    t.set_editor_property('cast_shadow', False)
    t.set_editor_property('hidden_in_game', False)         # the graph grows it from zero length at the muzzle
    t.set_editor_property('relative_rotation', unreal.Rotator(roll=0.0, pitch=90.0, yaw=0.0))   # cylinder Z -> bullet axis
    t.set_editor_property('relative_scale3d', unreal.Vector(0.02, 0.02, 0.0))                    # zero length at spawn; the tick graph sets it
    t.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 0.0))                      # (graph: -length/2, trailing the round)
    p = obj('Ballistics')
    p.set_editor_property('initial_speed', float(B['muzzle_cms']))
    p.set_editor_property('max_speed', 0.0)
    p.set_editor_property('projectile_gravity_scale', 1.0)
    p.set_editor_property('rotation_follows_velocity', True)
    p.set_editor_property('should_bounce', False)
    del s, t, p
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property('initial_life_span', 4.0); del cdo
    R['status'] = str(bp.get_editor_property('status')); R['saved'] = eal.save_loaded_asset(bp, False)
    del bp, mat
    # ---- input
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
    p = '/Game/Furina/Input/IA_FurinaFireAuto'
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset('IA_FurinaFireAuto', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); ia.set_editor_property('triggers', [])
    eal.save_loaded_asset(ia, False)
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                           for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    if ('LeftMouseButton', 'IA_FurinaFireAuto') not in listing(): imc.map_key(ia, key('LeftMouseButton'))
    single = unreal.load_asset('/Game/Furina/Input/IA_FurinaFire')
    if ('LeftMouseButton', 'IA_FurinaFire') in listing(): imc.unmap_key(single, key('LeftMouseButton'))
    eal.save_loaded_asset(imc, False)
    R['lmb'] = [m for m in listing() if m[0] == 'LeftMouseButton']
    del imc, ia, single
    json.dump(R, open(DATA + r'\fp_bullet_setup.json', 'w'), indent=1, default=str)
    print('FP_BULLET_SETUP', R)
main()
del main
