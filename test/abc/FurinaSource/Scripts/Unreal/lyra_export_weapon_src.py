"""에디터(편집 전용, 2026-11-23): 무기 정리본 SM_DE_<키>(언리얼 정적 메시) -> FurinaSource/FBX/Weapons/_export/SM_DE_<키>.fbx (+ .slots.json)
 이유: 1인칭 뷰모델 Blender 스크립트(fpvm_lib.load_weapon)가 읽는 원본 폴더(Downloads/FurinaWeaponSrc/Germany/_export)가 이 PC 에 없음.
 FBX 내보내기는 재질 '에셋' 이름을 쓰므로(슬롯 이름이 아님), 임시 복제 메시에 슬롯마다 다른 임시 재질(M_S00..)을 걸어 내보내고
 슬롯 이름 표를 .slots.json 에 남김 -> fpvm_lib.load_weapon 이 Blender 에서 재질 이름을 원래 슬롯 이름으로 되돌림. 임시 에셋은 지움.
 사용: ue_remote_run.py lyra_export_weapon_src.py [키+키...]   (없으면 Germany 폴더 전부)"""
import json, sys, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); OUTD = ROOT / 'FurinaSource' / 'FBX' / 'Weapons' / '_export'; OUTD.mkdir(parents=True, exist_ok=True)
ASSETS = unreal.EditorAssetLibrary; TMP = '/Game/_TmpWeaponExport'; R = {}
only = [a for a in sys.argv[1:] if not a.endswith('.py')]
keys = only[0].split('+') if only else None
ar = unreal.AssetRegistryHelpers.get_asset_registry()
found = {}
for a in ar.get_assets_by_path('/Game/Furina/Weapons/Germany', recursive=True):
    n = str(a.asset_name)
    if n.startswith('SM_DE_') and str(a.asset_class_path.asset_name) == 'StaticMesh': found[n[6:]] = str(a.package_name)
try:
    base_mat = unreal.load_asset('/Engine/EngineMaterials/WorldGridMaterial')
    for key in sorted(keys or found):
        try:
            src = found[key]; tmp = f'{TMP}/SM_DE_{key}'
            if ASSETS.does_asset_exist(tmp): ASSETS.delete_asset(tmp)
            assert ASSETS.duplicate_asset(src, tmp); m = unreal.load_asset(tmp)
            ns = m.get_editor_property('nanite_settings')
            if ns.enabled:   # Nanite 메시는 FBX 로 '줄인 대체 메시'가 나감(MP38 탄창·ZF39/41 부품 빠짐) -> 임시 복제본에서 끄고 원래 삼각형으로
                ns.enabled = False; m.set_editor_property('nanite_settings', ns)   # set_editor_property -> PostEditChange -> 다시 빌드
            mats = list(m.static_materials); table = []
            for i, s in enumerate(mats):
                mp = f'{TMP}/M_S{i:02d}'
                mi = unreal.load_asset(mp) if ASSETS.does_asset_exist(mp) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(f'M_S{i:02d}', TMP, unreal.Material, unreal.MaterialFactoryNew())
                table.append({'tmp': f'M_S{i:02d}', 'slot': str(s.material_slot_name), 'material': s.material_interface.get_name() if s.material_interface else None})
                s.material_interface = mi
            m.set_editor_property('static_materials', mats)
            t = unreal.AssetExportTask(); t.object = m; t.filename = str(OUTD / f'SM_DE_{key}.fbx'); t.automated = True; t.prompt = False; t.replace_identical = True
            o = unreal.FbxExportOption(); o.collision = False; o.level_of_detail = False; o.ascii = False; o.vertex_color = True
            try: o.set_editor_property('force_front_x_axis', False)
            except Exception: pass
            t.options = o; ok = unreal.Exporter.run_asset_export_task(t)
            (OUTD / f'SM_DE_{key}.slots.json').write_text(json.dumps(table, indent=1, ensure_ascii=False), encoding='utf-8')
            b = m.get_bounding_box(); R[key] = {'ok': ok, 'slots': len(table), 'tris': m.get_num_triangles(0), 'min': [round(b.min.x, 2), round(b.min.y, 2), round(b.min.z, 2)], 'max': [round(b.max.x, 2), round(b.max.y, 2), round(b.max.z, 2)]}
        except Exception: R[key] = {'error': traceback.format_exc()[-400:]}
finally:
    if ASSETS.does_directory_exist(TMP): ASSETS.delete_directory(TMP)
(ROOT / 'Saved' / 'WeaponSrcExport.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8'); print('WEAPON_SRC', json.dumps(R, ensure_ascii=False)[:3000])
