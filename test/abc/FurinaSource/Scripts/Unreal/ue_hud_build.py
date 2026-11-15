"""Self-made HUD assets (2026-11-15), replaces the supplied M4 HUD frame image:
 - /Game/Furina/UI/T_M4HUDSilhouette  (Textures/M4HUD_Silhouette.png, white side-view silhouette rendered from our SK_M4A1 + SM_M4Mag by render_m4_hud_silhouette.py)
 - /Game/Furina/UI/MPC_FurinaHUD      (scalars Ammo, Reserve, Reloading, written every frame by BP_FurinaHUD)
 - /Game/Furina/UI/M_FurinaHUD        (unlit translucent; one Custom HLSL node draws the whole panel: chamfered plate, silhouette, 30 round pips, seven-segment ammo / reserve digits)
 usage: py ue_hud_build.py   (re-run to rebuild the material after editing HLSL below)"""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SRC = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Textures\M4HUD_Silhouette.png'
HLSL = r'''
float2 p = float2(UV.x * 3.0, UV.y);
float3 ink = float3(0.80, 0.96, 1.0);
float3 acc = float3(0.20, 0.72, 1.0);
float3 warn = float3(1.0, 0.45, 0.12);
float ammoI = clamp(floor(Ammo + 0.5), 0.0, 99.0);
float resI = clamp(floor(Reserve + 0.5), 0.0, 999.0);
float low = (ammoI <= 8.0) ? 1.0 : 0.0;
float3 mainc = lerp(ink, warn, low);
float aa = 0.006;
// plate: rectangle with the top-left and bottom-right corners cut
float2 dq = abs(p - float2(1.5, 0.5)) - float2(1.48, 0.48);
float dBox = -max(dq.x, dq.y);
float dC1 = (p.x + p.y - 0.30) * 0.7071;
float dC2 = ((3.0 - p.x) + (1.0 - p.y) - 0.30) * 0.7071;
float di = min(dBox, min(dC1, dC2));
float fill = smoothstep(0.0, aa, di);
float edge = fill * (1.0 - smoothstep(0.012, 0.012 + aa, di));
float cutE = fill * (1.0 - smoothstep(0.030, 0.030 + aa, min(dC1, dC2)));
float3 col = float3(0.015, 0.04, 0.075);
float alpha = fill * 0.62;
col = lerp(col, acc, edge); alpha = max(alpha, edge * 0.95);
col = lerp(col, ink, cutE); alpha = max(alpha, cutE);
// divider between weapon and counters
float dv = (1.0 - smoothstep(0.004, 0.004 + aa, abs(p.x - 1.47))) * step(0.17, p.y) * step(p.y, 0.74);
col = lerp(col, acc, dv * 0.6); alpha = max(alpha, dv * 0.55);
// weapon silhouette (our own M4 model)
float su = (p.x - 0.14) / 1.27; float sv = (p.y - 0.30) / (1.27 / 3.3333);
float insd = step(0.0, su) * step(su, 1.0) * step(0.0, sv) * step(sv, 1.0);
float4 tx = Texture2DSample(Tex, TexSampler, float2(saturate(su), saturate(sv)));
float sa = tx.a * insd;
col = lerp(col, ink, sa); alpha = max(alpha, sa * 0.95);
// round pips: 30 bars, filled = rounds in the magazine; while reloading a light runs along them
for (int i = 0; i < 30; i++)
{
    float x0 = 0.17 + i * 0.0875;
    float m = step(x0, p.x) * step(p.x, x0 + 0.060) * step(0.855, p.y) * step(p.y, 0.915);
    float lit = (i + 0.5 < Ammo) ? 1.0 : 0.0;
    // reloading: the pips fill from empty to full in step with the reload time (ReloadP 0..1 = elapsed / reload duration), the pip being filled fades in
    if (Reload > 0.5) lit = saturate(ReloadP * 30.0 - i);
    float3 pc = lerp(float3(0.16, 0.26, 0.36), (Reload > 0.5) ? ink : mainc, lit);
    col = lerp(col, pc, m); alpha = max(alpha, m * lerp(0.45, 1.0, lit));
}
// seven-segment digits (slanted): ammo 2 digits big, reserve 3 digits small; unlit segments stay as a faint ghost
float ox[5] = {1.55, 1.81, 2.27, 2.42, 2.57};
float oy[5] = {0.24, 0.24, 0.40, 0.40, 0.40};
float dw[5] = {0.19, 0.19, 0.10, 0.10, 0.10};
float dh[5] = {0.36, 0.36, 0.20, 0.20, 0.20};
float dt[5] = {0.042, 0.042, 0.024, 0.024, 0.024};
float vals[5];
vals[0] = floor(ammoI / 10.0); vals[1] = fmod(ammoI, 10.0);
vals[2] = floor(resI / 100.0); vals[3] = fmod(floor(resI / 10.0), 10.0); vals[4] = fmod(resI, 10.0);
float blank[5];
blank[0] = (ammoI < 10.0) ? 1.0 : 0.0; blank[1] = 0.0;
blank[2] = (resI < 100.0) ? 1.0 : 0.0; blank[3] = (resI < 10.0) ? 1.0 : 0.0; blank[4] = 0.0;
int pat[10] = {63, 6, 91, 79, 102, 109, 125, 7, 127, 111};
for (int k = 0; k < 5; k++)
{
    float w = dw[k]; float h = dh[k]; float t = dt[k]; float g = t * 0.35;
    float2 lp = p - float2(ox[k], oy[k]);
    lp.x += (h * 0.5 - lp.y) * 0.10;
    float4 sg[7];
    sg[0] = float4(t * 0.8, 0.0, w - t * 0.8, t);
    sg[1] = float4(w - t, g + t * 0.5, w, h * 0.5 - g);
    sg[2] = float4(w - t, h * 0.5 + g, w, h - t * 0.5 - g);
    sg[3] = float4(t * 0.8, h - t, w - t * 0.8, h);
    sg[4] = float4(0.0, h * 0.5 + g, t, h - t * 0.5 - g);
    sg[5] = float4(0.0, g + t * 0.5, t, h * 0.5 - g);
    sg[6] = float4(t * 0.8, h * 0.5 - t * 0.5, w - t * 0.8, h * 0.5 + t * 0.5);
    int bits = pat[(int)vals[k]];
    for (int s = 0; s < 7; s++)
    {
        float m = step(sg[s].x, lp.x) * step(lp.x, sg[s].z) * step(sg[s].y, lp.y) * step(lp.y, sg[s].w);
        float on = (((bits >> s) & 1) == 1 && blank[k] < 0.5) ? 1.0 : 0.0;
        float3 dc = (k >= 2) ? ink : mainc;   // only the magazine count turns orange when low
        col = lerp(col, dc, m * on); alpha = max(alpha, m * lerp(0.13, 1.0, on));
    }
}
// slash between magazine and reserve
float2 sa0 = float2(2.235, 0.40); float2 sb0 = float2(2.165, 0.62);
float2 pa = p - sa0; float2 ba = sb0 - sa0;
float hh = saturate(dot(pa, ba) / dot(ba, ba));
float dl = length(pa - ba * hh);
float sl = 1.0 - smoothstep(0.010, 0.010 + aa, dl);
col = lerp(col, acc, sl); alpha = max(alpha, sl);
return float4(col, alpha);
'''
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools(); M = unreal.MaterialEditingLibrary; dest = '/Game/Furina/UI'
    tp = dest + '/T_M4HUDSilhouette'
    if not E.does_asset_exist(tp):
        task = unreal.AssetImportTask(); task.filename = SRC; task.destination_path = dest; task.destination_name = 'T_M4HUDSilhouette'; task.automated = True; task.save = True; T.import_asset_tasks([task])
    tex = unreal.load_asset(tp); assert tex, 'texture'
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON); tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('never_stream', True); tex.set_editor_property('srgb', True); E.save_loaded_asset(tex, False)
    mp = dest + '/MPC_FurinaHUD'
    mpc = unreal.load_asset(mp) if E.does_asset_exist(mp) else T.create_asset('MPC_FurinaHUD', dest, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    assert mpc, 'mpc'
    ps = []
    for n, v in (('Ammo', 30.0), ('Reserve', 120.0), ('Reloading', 0.0), ('ReloadP', 0.0)):
        p = unreal.CollectionScalarParameter(); p.set_editor_property('parameter_name', n); p.set_editor_property('default_value', v); ps.append(p)
    mpc.set_editor_property('scalar_parameters', ps); E.save_loaded_asset(mpc, False)
    p = dest + '/M_FurinaHUD'
    mat = unreal.load_asset(p) if E.does_asset_exist(p) else T.create_asset('M_FurinaHUD', dest, unreal.Material, unreal.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    mat.set_editor_property('material_domain', unreal.MaterialDomain.MD_SURFACE); mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT); mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    uv = M.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    time = M.create_material_expression(mat, unreal.MaterialExpressionTime, -900, 400)
    tobj = M.create_material_expression(mat, unreal.MaterialExpressionTextureObject, -900, 500); tobj.set_editor_property('texture', tex)
    cps = {}
    for i, n in enumerate(('Ammo', 'Reserve', 'Reloading', 'ReloadP')):
        c = M.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, -900, 120 + 90 * i); c.set_editor_property('collection', mpc); c.set_editor_property('parameter_name', n); cps[n] = c
    custom = M.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, 0); custom.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    inputs = []
    for n in ('UV', 'Ammo', 'Reserve', 'Reload', 'ReloadP', 'Time', 'Tex'):
        i = unreal.CustomInput(); i.set_editor_property('input_name', n); inputs.append(i)
    custom.set_editor_property('inputs', inputs); custom.set_editor_property('code', HLSL.strip())
    for a, b in ((uv, 'UV'), (cps['Ammo'], 'Ammo'), (cps['Reserve'], 'Reserve'), (cps['Reloading'], 'Reload'), (cps['ReloadP'], 'ReloadP'), (time, 'Time'), (tobj, 'Tex')):
        assert M.connect_material_expressions(a, '', custom, b), b
    rgb = M.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, -60); rgb.set_editor_property('r', True); rgb.set_editor_property('g', True); rgb.set_editor_property('b', True); rgb.set_editor_property('a', False)
    al = M.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 100); al.set_editor_property('r', False); al.set_editor_property('g', False); al.set_editor_property('b', False); al.set_editor_property('a', True)
    assert M.connect_material_expressions(custom, '', rgb, ''); assert M.connect_material_expressions(custom, '', al, '')
    assert M.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR); assert M.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY)
    M.recompile_material(mat); R['mat_saved'] = E.save_loaded_asset(mat, False); R['ok'] = True
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'hud_build.json'), 'w'), indent=1); print('HUD_BUILD', R.get('ok'), R.get('error', '')[-300:])
