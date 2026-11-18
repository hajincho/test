"""Lyra 에디터(`py <파일> [fit]`, PIE 중지 상태): SM_M4Mag 바닥판(탄창 하단)이 기울어 잘려 있는 것을 수평으로 편다.
옆 렌더에서 탄창 좌/우 옆면은 수직인데 바닥 가장자리가 ~7도 기울어(앞쪽이 높고 뒤쪽이 낮음) 탄창이 삐뚤게 꽂힌 것처럼 보였다.
방법: 가장 낮은 띠(zmin ~ zmin+BAND)의 정점으로 평면 z = a + b*y + c*x 를 맞추고, 삽입구 아래 구간(z < Z_TOP)에서 z -= (b*(y-yc) + c*(x-xc)) * w(z) 로 전단(shear)한다.
 w 는 Z_TOP 에서 0 -> 최저점에서 1. x,y 는 그대로라 옆면은 수직을 유지하고 삽입구 안쪽(z >= Z_TOP)은 변하지 않는다.
`fit` 인자: 계산만 하고 메시는 바꾸지 않는다. 적용 전 원본을 /Game/Furina/Backups/SM_M4Mag_pre_level 로 복제해 **디스크에 저장**해 두고, 항상 그 백업에서 다시 계산한다(여러 번 실행해도 누적 안 됨).
-> Data/lyra_mag_level.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_level.json'
Z_TOP = -4.5; BAND = 0.4
EAL = unreal.EditorAssetLibrary
R = {}
def fit_plane(pts):
    # 최소제곱 z = a + b*y + c*x  (3x3 정규방정식, 순수 파이썬)
    n = len(pts); sx = sy = sz = sxx = syy = sxy = sxz = syz = 0.0
    for x, y, z in pts: sx += x; sy += y; sz += z; sxx += x * x; syy += y * y; sxy += x * y; sxz += x * z; syz += y * z
    A = [[n, sy, sx], [sy, syy, sxy], [sx, sxy, sxx]]; B = [sz, syz, sxz]
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(A[r][i])); A[i], A[p] = A[p], A[i]; B[i], B[p] = B[p], B[i]
        for r in range(i + 1, 3):
            f = A[r][i] / A[i][i]
            for c in range(i, 3): A[r][c] -= f * A[i][c]
            B[r] -= f * B[i]
    s = [0.0] * 3
    for i in (2, 1, 0): s[i] = (B[i] - sum(A[i][j] * s[j] for j in range(i + 1, 3))) / A[i][i]
    return s  # a, b(y), c(x)
try:
    SRC = '/Game/Furina/M4/SM_M4Mag'; BAK = '/Game/Furina/Backups/SM_M4Mag_pre_level'
    if not EAL.does_asset_exist(BAK):
        R['backup'] = bool(EAL.duplicate_asset(SRC, BAK)); R['backup_saved'] = bool(EAL.save_asset(BAK, False))
    bak = unreal.load_asset(BAK); sm = unreal.load_asset(SRC)
    sd_b = bak.get_static_mesh_description(0); sd = sm.get_static_mesh_description(0)
    n = sd_b.get_vertex_count(); assert n == sd.get_vertex_count(); R['n'] = n
    P = []
    for i in range(n):
        p = sd_b.get_vertex_position(unreal.VertexID(i)); P.append((p.x, p.y, p.z))
    zmin = min(p[2] for p in P); R['zmin'] = round(zmin, 3)
    low = [p for p in P if p[2] < zmin + BAND]; R['n_low'] = len(low)
    # 이상치 방지: 한 번 맞춘 뒤 평면에서 0.15cm 이내인 점으로 다시 맞춤
    a, b, c = fit_plane(low)
    low2 = [p for p in low if abs(p[2] - (a + b * p[1] + c * p[0])) < 0.15]; a, b, c = fit_plane(low2); R['n_low_fit'] = len(low2)
    import math
    R['plane'] = {'a': round(a, 4), 'b_per_y': round(b, 4), 'c_per_x': round(c, 4), 'tilt_deg_y': round(math.degrees(math.atan(b)), 2), 'tilt_deg_x': round(math.degrees(math.atan(c)), 2)}
    if 'revert' in sys.argv: a = b = c = 0.0; R['revert'] = True  # 전단 0 = 백업(수평 보정 전) 그대로
    xc = sum(p[0] for p in low2) / len(low2); yc = sum(p[1] for p in low2) / len(low2); R['center'] = [round(xc, 3), round(yc, 3)]
    if 'fit' not in sys.argv:
        for i, (x, y, z) in enumerate(P):
            w = min(1.0, max(0.0, (Z_TOP - z) / (Z_TOP - zmin)))
            dz = (b * (y - yc) + c * (x - xc)) * w
            sd.set_vertex_position(unreal.VertexID(i), unreal.Vector(x, y, z - dz))
        sm.build_from_static_mesh_descriptions([sd], False)
        bb = sm.get_bounds(); R['bounds_after'] = {'origin': [round(bb.origin.x, 2), round(bb.origin.y, 2), round(bb.origin.z, 2)], 'extent': [round(bb.box_extent.x, 2), round(bb.box_extent.y, 2), round(bb.box_extent.z, 2)]}
        # 적용 후 같은 방식으로 다시 측정
        sd2 = sm.get_static_mesh_description(0); P2 = []
        for i in range(sd2.get_vertex_count()):
            p = sd2.get_vertex_position(unreal.VertexID(i)); P2.append((p.x, p.y, p.z))
        zm2 = min(p[2] for p in P2); low3 = [p for p in P2 if p[2] < zm2 + BAND]; a2, b2, c2 = fit_plane(low3)
        R['after'] = {'zmin': round(zm2, 3), 'tilt_deg_y': round(math.degrees(math.atan(b2)), 2), 'tilt_deg_x': round(math.degrees(math.atan(c2)), 2)}
        R['saved'] = bool(EAL.save_loaded_asset(sm, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_LEVEL', R)
