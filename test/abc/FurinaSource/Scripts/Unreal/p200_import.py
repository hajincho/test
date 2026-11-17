"""P200: 분리된 glTF(슬라이드/프레임) + 텍스처 임포트, 마스터 머티리얼 M_P200 생성, 메시에 적용.
(열린 에디터에서 Remote Execution 으로 실행)  결과 -> /Game/Furina/P200/{SM_P200_Slide, SM_P200_Frame, M_P200, T_P200_*}"""
import unreal, os, json, traceback
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
ROOT = '/Game/Furina/P200'; SRC = r'L:\Saved\Scratch\p200'
TEX = r'C:\Users\fromj\Downloads\p200-pistol\textures'
R = {'log': []}
def task(path, dest, name=None):
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path); t.set_editor_property('destination_path', dest)
    t.set_editor_property('automated', True); t.set_editor_property('save', False); t.set_editor_property('replace_existing', True)
    if name: t.set_editor_property('destination_name', name)
    return t
def run():
    for p in (ROOT + '/Test',):
        if EAL.does_directory_exist(p): EAL.delete_directory(p)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    # ---- 메시
    tasks = [task(os.path.join(SRC, 'P200_slide.gltf'), ROOT + '/_imp'), task(os.path.join(SRC, 'P200_frame.gltf'), ROOT + '/_imp')]
    tools.import_asset_tasks(tasks)
    for part, nm in (('slide', 'SM_P200_Slide'), ('frame', 'SM_P200_Frame')):
        src = '%s/_imp/P200_%s/StaticMeshes/P200_%s' % (ROOT, part, part)
        assert EAL.does_asset_exist(src), 'import failed ' + src
        if EAL.does_asset_exist(ROOT + '/' + nm): EAL.delete_asset(ROOT + '/' + nm)
        assert EAL.rename_asset(src, ROOT + '/' + nm), 'rename ' + nm
    if EAL.does_directory_exist(ROOT + '/_imp'): EAL.delete_directory(ROOT + '/_imp')
    # ---- 텍스처
    names = {'albedo': ('DefaultMaterial_albedo.jpeg', 'T_P200_Albedo'), 'metallic': ('DefaultMaterial_metallic.jpeg', 'T_P200_Metallic'),
             'normal': ('DefaultMaterial_normal.png', 'T_P200_Normal'), 'rough': ('DefaultMaterial_roughness.jpeg', 'T_P200_Roughness')}
    tt = [task(os.path.join(TEX, f), ROOT, n) for f, n in names.values()]
    tools.import_asset_tasks(tt)
    T = {}
    for k, (f, n) in names.items():
        tex = unreal.load_asset('%s/%s' % (ROOT, n)); assert tex, n
        if k == 'normal':
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); tex.set_editor_property('srgb', False)
        elif k in ('metallic', 'rough'):
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb', False)
        EAL.save_loaded_asset(tex, False); T[k] = tex
    # ---- 머티리얼
    mp = ROOT + '/M_P200'
    if EAL.does_asset_exist(mp): EAL.delete_asset(mp)
    mat = tools.create_asset('M_P200', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    def tex_node(tex, x, y, sampler):
        n = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, x, y)
        n.set_editor_property('texture', tex); n.set_editor_property('sampler_type', sampler); return n
    a = tex_node(T['albedo'], -600, -300, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    me = tex_node(T['metallic'], -600, 0, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    ro = tex_node(T['rough'], -600, 300, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    no = tex_node(T['normal'], -600, 600, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(a, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(me, 'R', unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(ro, 'R', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(no, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(mat); EAL.save_loaded_asset(mat, False)
    for nm in ('SM_P200_Slide', 'SM_P200_Frame'):
        sm = unreal.load_asset(ROOT + '/' + nm)
        sm.set_material(0, mat)
        b = sm.get_bounds(); R['log'].append([nm, 'origin', str(b.origin), 'extent', str(b.box_extent), 'tris', sm.get_num_triangles(0) if hasattr(sm, 'get_num_triangles') else '?'])
        EAL.save_loaded_asset(sm, False)
    return 'ok'
try: R['result'] = run()
except Exception: R['error'] = traceback.format_exc()
print('P200_IMPORT', json.dumps(R, default=str, ensure_ascii=False)[:1500])
