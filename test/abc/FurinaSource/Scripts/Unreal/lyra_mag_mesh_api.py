"""Lyra 에디터: SM_M4Mag 정점 편집 API 가능 여부 점검 -> Data/lyra_mag_mesh_api.json"""
import unreal, json, traceback
R = {}
try:
    sm = unreal.load_asset('/Game/Furina/M4/SM_M4Mag')
    R['sm_methods'] = [n for n in dir(sm) if 'description' in n.lower() or 'vertex' in n.lower() or 'lod' in n.lower()][:30]
    sd = sm.get_static_mesh_description(0) if hasattr(sm, 'get_static_mesh_description') else None
    R['has_desc'] = sd is not None
    if sd is not None:
        R['desc_methods'] = [n for n in dir(sd) if 'vertex' in n.lower() or 'position' in n.lower()][:40]
    R['libs'] = [n for n in dir(unreal) if 'MeshDescription' in n or 'StaticMeshEditor' in n or 'GeometryScript' in n][:30]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_mesh_api.json', 'w'), indent=1); print('LYRA_MAG_API', R.get('has_desc'), R.get('error', '')[-120:])
