"""헤드리스: 독일 무기 21종 가져오기 (모션 없음, 메시+머티리얼만).
 입력: Downloads/FurinaWeaponSrc/Germany/_export/SM_DE_<키>.fbx (Blender 정리본: 총구 UE +Y, 위 +Z, 실제 크기 cm, 원점 = 경계 중심), Data/de_weapons_texmap.json
 출력: /Game/Furina/Weapons/Germany/<키>/SM_DE_<키>, Textures/T_*, MI_DE_<키>_<슬롯>; 공용 /Game/Furina/Weapons/Materials/M_FurinaWeaponPBR (+ 기본 텍스처)
 인자: [키,...] (없으면 전부)   -> Data/lyra_de_weapons_import.json"""
import unreal, json, sys, os, re, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; ONLY = ARGS[0].split(',') if ARGS else None
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; EXP = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export'; DEF = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\_defaults'
TM = json.load(open(D + r'\de_weapons_texmap.json', encoding='utf-8')); BJ = json.load(open(D + r'\de_weapons_build.json', encoding='utf-8'))
# 소총+조준경 합본(de_scoped_build.py): 소총 재질은 원본 항목('@rifle') 재사용 + 조준경/마운트 단색
if os.path.exists(D + r'\de_scoped_texmap.json'):
    for k, v in json.load(open(D + r'\de_scoped_texmap.json', encoding='utf-8')).items():
        TM[k] = dict(TM.get(v.pop('@rifle'), {})); TM[k].update(v)
    BJ.update(json.load(open(D + r'\de_scoped_build.json', encoding='utf-8')))
AT = unreal.AssetToolsHelpers.get_asset_tools(); EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
BASE = '/Game/Furina/Weapons'; R = {'weapons': {}}
def asc(s): return re.sub(r'[^A-Za-z0-9_]', '_', s.replace('х', 'x'))
def imp_tex(path, dest, name, kind, gl=False):
    full = dest + '/' + name
    if not EAL.does_asset_exist(full):
        t = unreal.AssetImportTask(); t.set_editor_property('filename', path); t.set_editor_property('destination_path', dest); t.set_editor_property('destination_name', name)
        t.set_editor_property('automated', True); t.set_editor_property('replace_existing', True); t.set_editor_property('save', False)
        AT.import_asset_tasks([t])
    tex = unreal.load_asset(full)
    if kind == 'normal':
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); tex.set_editor_property('srgb', False); tex.set_editor_property('flip_green_channel', bool(gl))
    elif kind in ('roughness', 'metallic', 'ao', 'mask'):
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb', False)
    else: tex.set_editor_property('srgb', True)
    EAL.save_loaded_asset(tex, False); return tex
def master():
    path = BASE + '/Materials/M_FurinaWeaponPBR'
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    dtx = {k: imp_tex(DEF + '\\' + f, BASE + '/Materials', n, kind) for k, f, n, kind in (('white', 'white.png', 'T_FW_White', 'color'), ('wmask', 'white.png', 'T_FW_WhiteMask', 'mask'), ('black', 'black.png', 'T_FW_BlackMask', 'mask'), ('normal', 'flatnormal.png', 'T_FW_FlatNormal', 'normal'))}
    m = AT.create_asset('M_FurinaWeaponPBR', BASE + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
    def tp(name, tex, st, x, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y); e.set_editor_property('parameter_name', name); e.set_editor_property('texture', tex); e.set_editor_property('sampler_type', st); return e
    def sp(name, v, x, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y); e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', v); return e
    def op(cls, a, ao, b, bo, x, y):
        e = MEL.create_material_expression(m, cls, x, y); MEL.connect_material_expressions(a, ao, e, 'A'); MEL.connect_material_expressions(b, bo, e, 'B'); return e
    bc = tp('BaseColorTex', dtx['white'], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -800, -300)
    tint = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -800, -120); tint.set_editor_property('parameter_name', 'Tint'); tint.set_editor_property('default_value', unreal.LinearColor(1, 1, 1, 1))
    MEL.connect_material_property(op(unreal.MaterialExpressionMultiply, bc, 'RGB', tint, '', -500, -250), '', unreal.MaterialProperty.MP_BASE_COLOR)
    nm = tp('NormalTex', dtx['normal'], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -800, 50); MEL.connect_material_property(nm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    for pname, prop, defs, y in (('Rough', unreal.MaterialProperty.MP_ROUGHNESS, (1.0, 0.0), 300), ('Metal', unreal.MaterialProperty.MP_METALLIC, (1.0, 0.0), 600)):
        t = tp(pname + 'Tex', dtx['wmask'] if pname == 'Rough' else dtx['black'], unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -800, y)
        mul = op(unreal.MaterialExpressionMultiply, t, 'R', sp(pname + 'Scale', defs[0], -800, y + 180), '', -500, y)
        add = op(unreal.MaterialExpressionAdd, mul, '', sp(pname + 'Add', defs[1], -500, y + 150), '', -300, y); MEL.connect_material_property(add, '', prop)
    ao = tp('AOTex', dtx['wmask'], unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -800, 950); MEL.connect_material_property(ao, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False); return m
def norm(s): return re.sub(r'[^0-9a-z]', '', s.lower().replace('х', 'x'))
def run():
    M = master(); R['master'] = M.get_path_name()
    for key, mats in TM.items():
        if ONLY and key not in ONLY: continue
        e = {}; dest = BASE + '/Germany/' + key
        try:
            ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
            ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False)
            sd = ui.get_editor_property('static_mesh_import_data'); tris = BJ.get(key, {}).get('tris', 0)
            for k, v in (('combine_meshes', True), ('generate_lightmap_u_vs', False), ('auto_generate_collision', False), ('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS), ('build_nanite', tris > 300000)):
                try: sd.set_editor_property(k, v)
                except Exception as ex: e.setdefault('opt_err', []).append(k)
            t = unreal.AssetImportTask(); t.set_editor_property('filename', EXP + '\\SM_DE_%s.fbx' % key); t.set_editor_property('destination_path', dest); t.set_editor_property('destination_name', 'SM_DE_' + key)
            t.set_editor_property('automated', True); t.set_editor_property('replace_existing', True); t.set_editor_property('save', False); t.set_editor_property('options', ui)
            AT.import_asset_tasks([t]); sm = unreal.load_asset(dest + '/SM_DE_' + key)
            e['nanite'] = tris > 300000; bb = sm.get_bounding_box(); e['size_cm'] = [round(bb.max.x - bb.min.x, 2), round(bb.max.y - bb.min.y, 2), round(bb.max.z - bb.min.z, 2)]
            slots = sm.get_editor_property('static_materials'); e['slots'] = []
            for i, st in enumerate(slots):
                sname = str(st.get_editor_property('material_slot_name')); mk = None
                for mn in mats:
                    if norm(mn) == norm(sname) or (mn == 'None' and len(mats) == 1): mk = mn; break
                if mk is None and len(mats) == 1: mk = list(mats)[0]
                spec = mats.get(mk, {}) if mk else {}
                mi = AT.create_asset('MI_DE_%s_%s' % (key, asc(sname)), dest, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()) if not EAL.does_asset_exist(dest + '/MI_DE_%s_%s' % (key, asc(sname))) else unreal.load_asset(dest + '/MI_DE_%s_%s' % (key, asc(sname)))
                mi.set_editor_property('parent', M); MEL.clear_all_material_instance_parameters(mi)   # 다시 가져올 때 예전 텍스처/값 남지 않게
                for kind, pname in (('basecolor', 'BaseColorTex'), ('normal', 'NormalTex'), ('roughness', 'RoughTex'), ('metallic', 'MetalTex'), ('ao', 'AOTex')):
                    if spec.get(kind):
                        tex = imp_tex(spec[kind], dest + '/Textures', 'T_DE_%s_%s' % (key, asc(os.path.splitext(os.path.basename(spec[kind]))[0].replace('.tga', ''))), kind, spec.get('normal_gl', False))
                        MEL.set_material_instance_texture_parameter_value(mi, pname, tex)
                if not spec.get('roughness'): MEL.set_material_instance_scalar_parameter_value(mi, 'RoughScale', 0.0); MEL.set_material_instance_scalar_parameter_value(mi, 'RoughAdd', spec['plain'][4] if spec.get('plain') else 0.55)
                if not spec.get('metallic'): MEL.set_material_instance_scalar_parameter_value(mi, 'MetalScale', 0.0); MEL.set_material_instance_scalar_parameter_value(mi, 'MetalAdd', spec['plain'][3] if spec.get('plain') else 0.0)
                if spec.get('plain'): MEL.set_material_instance_vector_parameter_value(mi, 'Tint', unreal.LinearColor(*spec['plain'][:3], 1))
                EAL.save_loaded_asset(mi, False); sm.set_material(i, mi); e['slots'].append([sname, mk, sorted(k for k in spec if k in ('basecolor', 'normal', 'roughness', 'metallic', 'ao', 'plain'))])
            e['saved'] = bool(EAL.save_loaded_asset(sm, False))
        except Exception: e['error'] = traceback.format_exc()[-700:]
        R['weapons'][key] = e; print('DE_IMPORT', key, e.get('size_cm'), e.get('error', '')[-200:])
        json.dump(R, open(D + r'\lyra_de_weapons_import.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
json.dump(R, open(D + r'\lyra_de_weapons_import.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str); print('LYRA_DE_IMPORT_DONE', R.get('error', '')[-300:])
