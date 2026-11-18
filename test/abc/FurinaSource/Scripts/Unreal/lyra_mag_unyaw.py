"""Lyra 에디터(`py <파일> [fit]`, PIE 중지 상태): SM_M4Mag 가 수직축(Z) 둘레로 약 8~9도 돌아가 있는(요 회전) 것을 바로잡는다.
발견: 아래에서 올려다본 화면에서 탄창 바닥판이 총 몸통 방향과 어긋나 있었다. Blender 로 원본 FBX 의 높이별 단면을 PCA 하면 모든 높이에서 장축이 Y 축에서 7.7~9.7도 돌아가 있다(삽입구는 좌우 대칭).
 예전 '좌우 0.33cm 치우침'도 이 회전 때문이었다.
방법: 디스크 백업 /Game/Furina/Backups/SM_M4Mag_pre_level (= lyra_mag_fit_mesh.py 적용본)에서 그 수정을 역산해 원본 정점을 복원
 (x0 = x/s(z) + 0.33, s 는 z -4.5~-3.5 에서 1 -> 0.8) -> 높이 -2~3cm 구간 PCA 로 요 각도를 구해 탄창 중심 둘레로 되돌려 돌림 -> 위쪽 구간 좌우 중심을 x=0 으로.
 폭을 줄이는 이전 수정(0.8배)은 더 이상 필요 없어 쓰지 않는다. 항상 백업에서 다시 계산(누적 안 됨). `fit` 인자: 계산만.
-> Data/lyra_mag_unyaw.json"""
import unreal, json, sys, math, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_unyaw.json'
EAL = unreal.EditorAssetLibrary
DX = -0.33; Z_LO = -4.5; Z_HI = -3.5; XS = 0.8   # lyra_mag_fit_mesh.py 와 같은 값(역산용)
R = {}
def pca_yaw(pts):
    n = len(pts); mx = sum(p[0] for p in pts) / n; my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n; syy = sum((p[1] - my) ** 2 for p in pts) / n; sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    return 0.5 * math.atan2(2 * sxy, syy - sxx), mx, my
def rot(P, th, cx, cy):
    c, s = math.cos(th), math.sin(th)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c, z) for x, y, z in P]
def slab_yaws(P):
    out = []
    z = -8.0
    while z < 3.5:
        pts = [p for p in P if z <= p[2] < z + 1.0]
        if len(pts) > 20: out.append([round(z, 1), round(math.degrees(pca_yaw(pts)[0]), 2)])
        z += 1.0
    return out
try:
    SRC = '/Game/Furina/M4/SM_M4Mag'; BAK = '/Game/Furina/Backups/SM_M4Mag_pre_level'
    bak = unreal.load_asset(BAK); sm = unreal.load_asset(SRC)
    sd_b = bak.get_static_mesh_description(0); sd = sm.get_static_mesh_description(0)
    n = sd_b.get_vertex_count(); assert n == sd.get_vertex_count(); R['n'] = n
    P = []
    for i in range(n):
        p = sd_b.get_vertex_position(unreal.VertexID(i)); z = p.z
        t = min(1.0, max(0.0, (z - Z_LO) / (Z_HI - Z_LO))); s = 1.0 + (XS - 1.0) * t
        P.append((p.x / s - DX, p.y, z))   # 원본 복원
    R['orig_x'] = [round(min(p[0] for p in P), 2), round(max(p[0] for p in P), 2)]
    R['orig_slab_yaw'] = slab_yaws(P)
    core = [p for p in P if -2.0 <= p[2] < 3.0]
    a, cx, cy = pca_yaw(core); R['yaw_deg'] = round(math.degrees(a), 3); R['center'] = [round(cx, 3), round(cy, 3)]
    # 회전 방향은 두 후보 중 남는 요가 작은 쪽
    best = None
    for th in (a, -a):
        Q = rot(P, th, cx, cy); res = abs(pca_yaw([q for q in Q if -2.0 <= q[2] < 3.0])[0])
        if best is None or res < best[0]: best = (res, th, Q)
    Q = best[2]; R['applied_rot_deg'] = round(math.degrees(best[1]), 3)
    up = [q for q in Q if q[2] >= -4.0]; xm = (min(q[0] for q in up) + max(q[0] for q in up)) / 2.0
    Q = [(x - xm, y, z) for x, y, z in Q]; R['x_shift'] = round(-xm, 3)
    R['after_slab_yaw'] = slab_yaws(Q)
    R['after_x_all'] = [round(min(q[0] for q in Q), 2), round(max(q[0] for q in Q), 2)]
    R['after_x_upper'] = [round(min(q[0] for q in Q if q[2] >= -4.0), 2), round(max(q[0] for q in Q if q[2] >= -4.0), 2)]
    if 'fit' not in sys.argv:
        for i, (x, y, z) in enumerate(Q): sd.set_vertex_position(unreal.VertexID(i), unreal.Vector(x, y, z))
        sm.build_from_static_mesh_descriptions([sd], False)
        bb = sm.get_bounds(); R['bounds_after'] = {'origin': [round(bb.origin.x, 2), round(bb.origin.y, 2), round(bb.origin.z, 2)], 'extent': [round(bb.box_extent.x, 2), round(bb.box_extent.y, 2), round(bb.box_extent.z, 2)]}
        R['saved'] = bool(EAL.save_loaded_asset(sm, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_UNYAW', R.get('yaw_deg'), R.get('error', '')[-200:])
