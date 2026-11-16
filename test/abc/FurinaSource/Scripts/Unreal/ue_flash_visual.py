"""Muzzle flash look (2026-11-15), part of the Niagara muzzle flash upgrade (the spark layer is ue_flash_niagara.py).
BP_M4Flash gets, besides the old cone: two crossed streak planes along the bore (M_MuzzleStreak) and a star disc facing the shooter (M_MuzzleStar). Both materials are additive unlit custom-HLSL
(procedural spiky star / tapered streak, white-yellow core -> orange edge, HDR) and vary per shot through the actor position as a random seed (the muzzle moves every shot).
usage: py ue_flash_visual.py [flip]   (flip 1 mirrors the streak along its length when the UV direction is reversed)  -> Data/flash_visual.json"""
import unreal, json, os, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; DEST = '/Game/Furina/M4'
FLIP = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
STREAK = r'''
float t = (Flip > 0.5) ? 1.0 - UV.y : UV.y;
float a = (UV.x - 0.5) * 2.0;
float s = frac(sin(dot(Seed.xyz, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float w = pow(saturate(1.0 - t), 0.9) * (0.20 + 0.12 * s);
w *= 1.0 + 0.2 * sin(t * 38.0 + s * 20.0);
float edge = exp(-pow(abs(a) / max(w, 0.02), 2.0) * 2.5);
float fade = pow(saturate(1.0 - t), 1.7);
float core = exp(-abs(a) / max(w * 0.4, 0.02));
float3 hot = float3(3.2, 2.4, 1.1);
float3 warm = float3(1.1, 0.42, 0.06);
float3 c = lerp(warm, hot, core * (1.0 - t));
return float4(c * edge * fade * 0.48, 1.0);   // x0.6: 40 % more transparent (2026-11-16)
'''
STAR = r'''
float2 p = (UV - 0.5) * 2.0;
float r = length(p);
float s = frac(sin(dot(Seed.xyz, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float ang = atan2(p.y, p.x) + s * 6.2831;
float sp = pow(abs(cos(ang * 2.5)), 10.0) * 0.85 + pow(abs(cos(ang * 4.5 + 1.1)), 18.0) * 0.55 + 0.16;
float len = sp * (0.8 + 0.2 * s);
float body = smoothstep(len, len * 0.05, r) * saturate(1.0 - r);
float core = exp(-r * r * 22.0);
float3 c = lerp(float3(1.5, 0.5, 0.07), float3(4.0, 3.0, 1.6), saturate(core * 1.4));
return float4(c * (body * 0.48 + core * 0.54), 1.0);   // x0.6: 40 % more transparent (2026-11-16)
'''
def build_mat(name, code, with_flip):
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); M = unreal.MaterialEditingLibrary
    p = DEST + '/' + name
    mat = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT); mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE); mat.set_editor_property('two_sided', True)
    uv = M.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -800, 0)
    seed = M.create_material_expression(mat, unreal.MaterialExpressionActorPositionWS, -800, 200)
    custom = M.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, 0); custom.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names = ['UV', 'Seed'] + (['Flip'] if with_flip else []); ins = []
    for n in names:
        i = unreal.CustomInput(); i.set_editor_property('input_name', n); ins.append(i)
    custom.set_editor_property('inputs', ins); custom.set_editor_property('code', code.strip())
    assert M.connect_material_expressions(uv, '', custom, 'UV'); assert M.connect_material_expressions(seed, '', custom, 'Seed')
    if with_flip:
        fl = M.create_material_expression(mat, unreal.MaterialExpressionConstant, -800, 400); fl.set_editor_property('r', FLIP); assert M.connect_material_expressions(fl, '', custom, 'Flip')
    rgb = M.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 0)
    for k, v in (('r', True), ('g', True), ('b', True), ('a', False)): rgb.set_editor_property(k, v)
    assert M.connect_material_expressions(custom, '', rgb, ''); assert M.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat); E.save_loaded_asset(mat, False); return mat
def main():
    R = {}
    E = unreal.EditorAssetLibrary; S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    streak = build_mat('M_MuzzleStreak', STREAK, True); star = build_mat('M_MuzzleStar', STAR, False)
    bp = unreal.load_asset(DEST + '/BP_M4Flash')
    def part(name, cls, parent):
        hs = {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
        if name not in hs:
            h, err = S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs.get(parent, next(iter(hs.values()))), new_class=cls, blueprint_context=bp)); assert not str(err), str(err); S.rename_subobject(h, unreal.Text(name)); hs[name] = h
        return L.get_associated_object(L.get_data(hs[name]))
    plane = unreal.load_asset('/Engine/BasicShapes/Plane')
    for name, mat, loc, rot, scale in (('FlashStreakA', streak, (0, 12, 0), unreal.Rotator(roll=0, pitch=0, yaw=0), (0.10, 0.24, 1)),
                                       ('FlashStreakB', streak, (0, 12, 0), unreal.Rotator(roll=0, pitch=90, yaw=0), (0.10, 0.24, 1)),
                                       ('FlashStar', star, (0, 1.5, 0), unreal.Rotator(roll=90, pitch=0, yaw=0), (0.17, 0.17, 1))):
        c = part(name, unreal.StaticMeshComponent, 'FXRoot'); c.set_static_mesh(plane); c.set_material(0, mat)
        c.set_editor_property('relative_location', unreal.Vector(*loc)); c.set_editor_property('relative_rotation', rot); c.set_editor_property('relative_scale3d', unreal.Vector(*scale))
        c.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE); c.set_collision_profile_name('NoCollision'); c.set_editor_property('cast_shadow', False)
    cone = part('FXMesh', unreal.StaticMeshComponent, 'FXRoot'); cone.set_editor_property('relative_scale3d', unreal.Vector(.03, .03, .10))
    cone.set_editor_property('hidden_in_game', True)      # the old solid cone looked like a red tooth next to the new additive layers; kept in the BP only as the component the death/cleanup code expects
    # an earlier session had already added solid opaque petals / core / ring meshes (M_MuzzleFlash, M_MuzzleFlashCore): they are the red teardrop and white disc seen in first person -> hidden, replaced by the additive layers
    for old in ('FlashPetalU', 'FlashPetalR', 'FlashPetalL', 'FlashPetalD', 'FlashCore', 'FlashRing'):
        c = part(old, unreal.StaticMeshComponent, 'FXRoot'); c.set_editor_property('hidden_in_game', True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'flash_visual.json'), 'w'), indent=1); print('FLASH_VISUAL', R.get('error', R.get('status'))[-300:])
