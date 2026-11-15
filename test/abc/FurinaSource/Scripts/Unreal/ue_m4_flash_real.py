"""More realistic muzzle flash (2026-11-15) for BP_M4Flash (spawned at the measured muzzle point with the rifle's rotation, rifle forward = local +Y):
 - FXMesh (existing cone): long forward tongue, orange
 - FlashCore: white-hot sphere at the muzzle (M_MuzzleFlashCore, emissive 38/30/14)
 - FlashPetalL/R/U/D: four short spikes fanned 38 deg off the barrel axis (the star of a 5.56 flash hider / expanding gas)
 - FlashRing: flattened sphere perpendicular to the barrel (side blast)
 - FlashLight: brighter and a little forward
 - BeginPlay: random roll around the barrel (0-360) and random size 0.8-1.3, so no two flashes look alike
Lifetime stays 0.045 s."""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
DEST = '/Game/Furina/M4'
def main():
    R = {}
    E = unreal.EditorAssetLibrary; ML = unreal.MaterialEditingLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    # core material
    p = DEST + '/M_MuzzleFlashCore'
    mat = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset('M_MuzzleFlashCore', DEST, unreal.Material, unreal.MaterialFactoryNew())
    ML.delete_all_material_expressions(mat); mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    c = ML.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0); c.set_editor_property('constant', unreal.LinearColor(38, 30, 14, 1))
    ML.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR); ML.recompile_material(mat); E.save_loaded_asset(mat, False); del c
    outer = unreal.load_asset(DEST + '/M_MuzzleFlash')
    bp = unreal.load_asset(DEST + '/BP_M4Flash')
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    def part(name, cls, parent='FXRoot'):
        hs = handles()
        if name not in hs:
            h, err = S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[parent], new_class=cls, blueprint_context=bp)); assert not str(err), str(err)
            S.rename_subobject(h, unreal.Text(name))
        return L.get_associated_object(L.get_data(handles()[name]))
    def shape(name, mesh, loc, scale, direction, material):
        c = part(name, unreal.StaticMeshComponent)
        c.set_static_mesh(unreal.load_asset(mesh)); c.set_material(0, material); c.set_collision_profile_name('NoCollision'); c.set_editor_property('cast_shadow', False)
        c.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('relative_location', unreal.Vector(*loc)); c.set_editor_property('relative_scale3d', unreal.Vector(*scale))
        c.set_editor_property('relative_rotation', unreal.MathLibrary.make_rot_from_z(unreal.MathLibrary.normal(unreal.Vector(*direction))))
        return c
    cone, sphere = '/Engine/BasicShapes/Cone', '/Engine/BasicShapes/Sphere'
    body = part('FXMesh', unreal.StaticMeshComponent)
    body.set_editor_property('relative_scale3d', unreal.Vector(0.05, 0.05, 0.22)); body.set_editor_property('relative_rotation', unreal.MathLibrary.make_rot_from_z(unreal.Vector(0, 1, 0)))
    shape('FlashCore', sphere, (0, 0.8, 0), (0.07, 0.09, 0.07), (0, 1, 0), mat)
    for name, d in (('FlashPetalL', (0.62, 1, 0)), ('FlashPetalR', (-0.62, 1, 0)), ('FlashPetalU', (0, 1, 0.62)), ('FlashPetalD', (0, 1, -0.62))):
        shape(name, cone, (0, 0.3, 0), (0.028, 0.028, 0.10), d, outer)
    shape('FlashRing', sphere, (0, 0.5, 0), (0.17, 0.012, 0.17), (0, 1, 0), outer)
    light = part('FlashLight', unreal.PointLightComponent)
    light.set_editor_property('intensity', 1800.0); light.set_editor_property('attenuation_radius', 220.0); light.set_editor_property('light_color', unreal.Color(255, 150, 55, 255))
    light.set_editor_property('relative_location', unreal.Vector(0, 8, 0)); light.set_editor_property('cast_shadows', False)
    del body, light
    # BeginPlay: random roll + size
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FlashRandRoll' not in nodes:
        def fn(name, path):
            n = ed.add_call_function_node(path); assert n, path; n.rename(name); return n
        def w(a, b):
            assert a.is_valid() and b.is_valid(); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b)
        begin = ed.find_event_node('ReceiveBeginPlay') or unreal.BlueprintEditorLibrary.add_event_override(bp, 'ReceiveBeginPlay', unreal.IntPoint(0, 0))
        ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); begin = ed.find_event_node('ReceiveBeginPlay')
        M = '/Script/Engine.KismetMathLibrary:'
        rr = fn('FlashRandRoll', M + 'RandomFloatInRange'); rr.find_input_pin('Min').set_pin_value('0'); rr.find_input_pin('Max').set_pin_value('360')
        mk = fn('FlashMakeRot', M + 'MakeRotator'); w(rr.find_result_pin(), mk.find_input_pin('Pitch'))        # pitch = rotation about local Y = the barrel axis
        add = fn('FlashRoll', '/Script/Engine.Actor:K2_AddActorLocalRotation'); w(mk.find_result_pin(), add.find_input_pin('DeltaRotation'))
        rs = fn('FlashRandSize', M + 'RandomFloatInRange'); rs.find_input_pin('Min').set_pin_value('0.8'); rs.find_input_pin('Max').set_pin_value('1.3')
        mv = fn('FlashMakeScale', M + 'MakeVector'); [w(rs.find_result_pin(), mv.find_input_pin(a)) for a in ('X', 'Y', 'Z')]
        sc = fn('FlashSetScale', '/Script/Engine.Actor:SetActorScale3D'); w(mv.find_result_pin(), sc.find_input_pin('NewScale3D'))
        old = list(begin.find_then_pin().list_connected_pins()); begin.find_then_pin().break_pin_links()
        w(begin.find_then_pin(), add.find_execute_pin()); w(add.find_then_pin(), sc.find_execute_pin())
        for q in old: w(sc.find_then_pin(), q)
        R['graph'] = 'added'
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    R['parts'] = sorted(handles().keys()); del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\m4_flash_real.json', 'w'), indent=1); print('M4_FLASH', R.get('status'), R.get('error', '')[:400])
