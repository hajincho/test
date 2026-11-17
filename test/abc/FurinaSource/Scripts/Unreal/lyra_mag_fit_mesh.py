"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): SM_M4Mag 정점을 고쳐 탄창이 삽입구 옆면 밖으로 튀어나와 리시버 측면을 덮는 문제를 없앤다.
원인(Blender 옆/앞 렌더 + 단면 측정, Data/mag_side.png, mag_front.png): 탄창 x 범위 [-1.18, 1.84] 가 삽입구 하우징 [-1.5, 1.5] 보다 +X(왼쪽)로 0.3cm 치우쳐 있어서
 하우징 높이 구간(z -4 ~ 3.4)의 탄창 옆면이 하우징 바깥으로 나와 회색 판처럼 보였다.
수정: (1) 모든 정점 x -= 0.33 (탄창 중심을 총 중심선에 맞춤)  (2) 하우징 안쪽 구간(z > -4)은 x 를 0.8배로 좁힘(z -4.5 ~ -3.5 에서 1 -> 0.8 로 부드럽게). 하우징 밖으로 나온 아래쪽 탄창 모양은 그대로.
원본은 /Game/Furina/Backups/SM_M4Mag_pre_fit 에 복제해 둔다. 이미 적용했으면(백업이 있으면) 백업에서 다시 계산한다(여러 번 실행해도 누적되지 않음).  -> Data/lyra_mag_fit_mesh.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_fit_mesh.json'
R = {}
DX = -0.33; Z_LO = -4.5; Z_HI = -3.5; XS = 0.8
EAL = unreal.EditorAssetLibrary
try:
    SRC = '/Game/Furina/M4/SM_M4Mag'; BAK = '/Game/Furina/Backups/SM_M4Mag_pre_fit'
    if not EAL.does_asset_exist(BAK):
        R['backup'] = bool(EAL.duplicate_asset(SRC, BAK)); R['backup_saved'] = bool(EAL.save_asset(BAK, False))  # 디스크에 저장해야 에디터를 닫아도 백업이 남는다
    bak = unreal.load_asset(BAK); sm = unreal.load_asset(SRC)
    sd_b = bak.get_static_mesh_description(0); sd = sm.get_static_mesh_description(0)
    n = sd.get_vertex_count(); R['n'] = n; R['n_bak'] = sd_b.get_vertex_count()
    assert n == sd_b.get_vertex_count(), 'vertex count mismatch'
    xs0 = []; xs1 = []
    for i in range(n):
        vid = unreal.VertexID(i); p = sd_b.get_vertex_position(vid)
        x, y, z = p.x + DX, p.y, p.z
        t = min(1.0, max(0.0, (z - Z_LO) / (Z_HI - Z_LO))); s = 1.0 + (XS - 1.0) * t
        x2 = x * s
        sd.set_vertex_position(vid, unreal.Vector(x2, y, z)); xs0.append(p.x); xs1.append(x2)
    R['x_before'] = [round(min(xs0), 2), round(max(xs0), 2)]; R['x_after'] = [round(min(xs1), 2), round(max(xs1), 2)]
    sm.build_from_static_mesh_descriptions([sd], False)
    b = sm.get_bounds(); R['bounds_after'] = {'origin': [round(b.origin.x, 2), round(b.origin.y, 2), round(b.origin.z, 2)], 'extent': [round(b.box_extent.x, 2), round(b.box_extent.y, 2), round(b.box_extent.z, 2)]}
    R['saved'] = bool(EAL.save_loaded_asset(sm, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_FIT', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
