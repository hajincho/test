"""HUD 권총 대응: ① P220 실루엣 텍스처 + MPC(Weapon, MagSize) + 머티리얼(실루엣 선택, 탄창 막대 수) ② BP_FurinaHUD (이름/모드 글자, 스칼라 전달).  열린 에디터에서 실행."""
import unreal, json, re, traceback
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; BEL = unreal.BlueprintEditorLibrary; PL = unreal.BlueprintGraphPinLibrary
KML = '/Script/Engine.KismetMathLibrary:'
R = {'log': []}
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-900:]])
def assets():
    dest = '/Game/Furina/UI'; tools = unreal.AssetToolsHelpers.get_asset_tools()
    t = unreal.AssetImportTask(); t.filename = r'L:\FurinaSource\Textures\P220HUD_Silhouette.png'; t.destination_path = dest; t.destination_name = 'T_P220HUDSilhouette'
    t.automated = True; t.save = False; t.replace_existing = True; tools.import_asset_tasks([t])
    tex = unreal.load_asset(dest + '/T_P220HUDSilhouette'); assert tex, 'tex'
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON); tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('never_stream', True); tex.set_editor_property('srgb', True); EAL.save_loaded_asset(tex, False)
    mpc = unreal.load_asset(dest + '/MPC_FurinaHUD'); ps = list(mpc.get_editor_property('scalar_parameters')); have = [str(p.get_editor_property('parameter_name')) for p in ps]
    for n, v in (('Weapon', 0.0), ('MagSize', 20.0)):
        if n not in have:
            p = unreal.CollectionScalarParameter(); p.set_editor_property('parameter_name', n); p.set_editor_property('default_value', v); ps.append(p)
    mpc.set_editor_property('scalar_parameters', ps); EAL.save_loaded_asset(mpc, False)
    mat = unreal.load_asset(dest + '/M_FurinaHUD'); code = None
    for ex in MEL.get_material_expressions(mat):
        if type(ex).__name__ == 'MaterialExpressionCustom': c = str(ex.get_editor_property('code')); code = c if code is None or len(c) > len(code) else code
    assert code and '(h * 0.5 - lp.y)' in code, 'hlsl'
    code = code.replace('float4 tx = Texture2DSample(Tex, TexSampler, float2(saturate(su), saturate(sv)));',
                        'float4 tx = (Weapon > 0.5) ? Texture2DSample(Tex2, Tex2Sampler, float2(saturate(su), saturate(sv))) : Texture2DSample(Tex, TexSampler, float2(saturate(su), saturate(sv)));')
    code = code.replace('float lit = (i + 0.5 < Ammo) ? 1.0 : 0.0;', 'float lit = ((i + 0.5) * (MagSize / 20.0) < Ammo) ? 1.0 : 0.0;')
    assert 'Tex2' in code and 'MagSize' in code, 'replace'
    open(r'L:\FurinaSource\Data\hud_custom_code_p220.hlsl', 'w', encoding='utf-8').write(code)
    tex1 = unreal.load_asset(dest + '/T_M4HUDSilhouette')
    MEL.delete_all_material_expressions(mat)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    time = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -900, 400)
    t1 = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureObject, -900, 500); t1.set_editor_property('texture', tex1)
    t2 = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureObject, -900, 700); t2.set_editor_property('texture', tex)
    cps = {}
    for i, n in enumerate(('Ammo', 'Reserve', 'Reloading', 'ReloadP', 'Weapon', 'MagSize')):
        c = MEL.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, -900, 120 + 90 * i); c.set_editor_property('collection', mpc); c.set_editor_property('parameter_name', n); cps[n] = c
    custom = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -400, 0); custom.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    inputs = []
    for n in ('UV', 'Ammo', 'Reserve', 'Reload', 'ReloadP', 'Time', 'Tex', 'Tex2', 'Weapon', 'MagSize'):
        i = unreal.CustomInput(); i.set_editor_property('input_name', n); inputs.append(i)
    custom.set_editor_property('inputs', inputs); custom.set_editor_property('code', code.strip())
    for a, b in ((uv, 'UV'), (cps['Ammo'], 'Ammo'), (cps['Reserve'], 'Reserve'), (cps['Reloading'], 'Reload'), (cps['ReloadP'], 'ReloadP'), (time, 'Time'), (t1, 'Tex'), (t2, 'Tex2'), (cps['Weapon'], 'Weapon'), (cps['MagSize'], 'MagSize')):
        assert MEL.connect_material_expressions(a, '', custom, b), b
    rgb = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, -60); rgb.set_editor_property('r', True); rgb.set_editor_property('g', True); rgb.set_editor_property('b', True); rgb.set_editor_property('a', False)
    al = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -150, 100); al.set_editor_property('r', False); al.set_editor_property('g', False); al.set_editor_property('b', False); al.set_editor_property('a', True)
    assert MEL.connect_material_expressions(custom, '', rgb, ''); assert MEL.connect_material_expressions(custom, '', al, '')
    assert MEL.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR); assert MEL.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(mat); return [EAL.save_loaded_asset(mat, False), len(MEL.get_material_expressions(mat))]
step('assets', assets)
print('P200_HUD_ASSETS', json.dumps(R, default=str, ensure_ascii=False)[:2000])
