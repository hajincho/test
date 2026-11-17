"""Lyra 에디터: SM_M4Mag / SK_M4A1 / SM_P220_* 에셋의 로컬 경계(박스 중심/반경), 정점/머티리얼 슬롯 수, 빌드 스케일/임포트 회전 -> Data/lyra_mag_asset_bounds.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_asset_bounds.json'
R = {}
try:
    for p in ('/Game/Furina/M4/SM_M4Mag', '/Game/Furina/M4/SK_M4A1', '/Game/Furina/P220/SM_P220_Frame', '/Game/Furina/P220/SM_P220_Slide'):
        a = unreal.load_asset(p)
        if a is None: R[p] = 'missing'; continue
        b = a.get_bounds(); row = {'origin': [round(b.origin.x, 2), round(b.origin.y, 2), round(b.origin.z, 2)], 'extent': [round(b.box_extent.x, 2), round(b.box_extent.y, 2), round(b.box_extent.z, 2)]}
        try: row['n_materials'] = len(a.get_editor_property('static_materials')) if isinstance(a, unreal.StaticMesh) else len(a.get_editor_property('materials'))
        except Exception: pass
        try: row['sockets'] = [str(s.get_editor_property('socket_name')) for s in a.get_editor_property('sockets')] if isinstance(a, unreal.StaticMesh) else None
        except Exception: pass
        R[p] = row
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_ASSET', R)
