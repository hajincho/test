"""에디터(편집 전용, 2026-11-22): 판처파우스트 60 모델(받은 panzerfaust-60.zip, FBX/Panzerfaust60/textures)의 재질
 1인칭 판처파우스트 메시(fpvm_panzerfaust60.py 로 들어간 같은 모델)의 'Panzerfaust60Surface' 슬롯이 비어 있었음
 -> 텍스처 4장(BaseColor/Normal/Roughness/Metallic) -> /Game/Furina/Weapons/Germany/panzerfaust60/, MI_DE_panzerfaust60(부모 M_FurinaWeaponPBR)
 -> SK_FPVM_PANZERFAUST 와 발사체 탄두 메시 SM_FPVM_PzfWarhead 의 같은 이름 슬롯에 지정. -> Saved/Pzf60Material.json"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); TEX = ROOT / 'FurinaSource' / 'FBX' / 'Panzerfaust60' / 'textures'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); MEL = unreal.MaterialEditingLibrary
DEST = '/Game/Furina/Weapons/Germany/panzerfaust60'
MAPS = {'BaseColor': ('BaseColorTex', True), 'Normal': ('NormalTex', False), 'Roughness': ('RoughTex', False), 'Metallic': ('MetalTex', False)}
try:
    texs = {}
    for k, (param, srgb) in MAPS.items():
        name = f'T_DE_panzerfaust60_{k}'
        t = unreal.AssetImportTask(); t.filename = str(TEX / f'Material.001_{k}.png'); t.destination_path = DEST; t.destination_name = name
        t.automated = True; t.save = False; t.replace_existing = True; TOOLS.import_asset_tasks([t])
        tx = unreal.load_asset(f'{DEST}/{name}'); assert tx, k
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP if k == 'Normal' else (unreal.TextureCompressionSettings.TC_DEFAULT if srgb else unreal.TextureCompressionSettings.TC_MASKS))
        tx.set_editor_property('srgb', srgb); assert ASSETS.save_loaded_asset(tx, False); texs[param] = tx
    path = f'{DEST}/MI_DE_panzerfaust60'
    mi = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else TOOLS.create_asset('MI_DE_panzerfaust60', DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset('/Game/Furina/Weapons/Materials/M_FurinaWeaponPBR'))
    for param, tx in texs.items(): MEL.set_material_instance_texture_parameter_value(mi, param, tx)
    assert ASSETS.save_loaded_asset(mi, False)
    for p in ('/Game/Furina/FPVM/PANZERFAUST/SK_FPVM_PANZERFAUST', '/Game/Furina/FP/SM_FPVM_PzfWarhead', '/Game/Furina/FPVM/PANZERFAUST/SM_FPVM_PzfWarhead'):
        a = unreal.load_asset(p) if ASSETS.does_asset_exist(p) else None
        if not a: continue
        if isinstance(a, unreal.SkeletalMesh):
            slots = list(a.materials); n = 0
            for s in slots:
                if str(s.material_slot_name) == 'Panzerfaust60Surface': s.material_interface = mi; n += 1
            a.set_editor_property('materials', slots)
        else:
            n = 0
            for i, s in enumerate(a.static_materials):
                if str(s.material_slot_name) == 'Panzerfaust60Surface': a.set_material(i, mi); n += 1
        assert ASSETS.save_loaded_asset(a, False); R[p] = n
except Exception: R['error'] = traceback.format_exc()[-1200:]
R['done'] = True; (ROOT / 'Saved' / 'Pzf60Material.json').write_text(json.dumps(R, indent=1), encoding='utf-8'); print('PZF60_MAT', R)
