"""Blender headless: compares the seated STANAG magazine faces of m4a1.001 (material stanag_mag) with the loose object mag_20rnd (and 'ammo'): principal axes / extents (PCA, world coords, units of the FBX) and a rigid
ICP fit of mag_20rnd onto the seated magazine (RMS residual after the fit) -> Data/colt_mag_analysis.json"""
import bpy, json, math
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx')
def world_verts(o, only_mat=None):
    M = np.array(o.matrix_world); me = o.data; idx = set()
    if only_mat:
        mats = [m.name if m else None for m in me.materials]
        for p in me.polygons:
            if mats[p.material_index] == only_mat: idx.update(p.vertices)
    else: idx = set(range(len(me.vertices)))
    P = np.array([me.vertices[i].co[:] for i in sorted(idx)]); return (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
def pca(P):
    c = P.mean(0); u, s, vt = np.linalg.svd(P - c, full_matrices=False); proj = (P - c) @ vt.T
    return dict(center=c.tolist(), axes=vt.tolist(), extent=(proj.max(0) - proj.min(0)).tolist())
seated = world_verts(bpy.data.objects['m4a1.001'], 'stanag_mag'); loose = world_verts(bpy.data.objects['mag_20rnd']); ammo = world_verts(bpy.data.objects['ammo'])
R = {'seated': pca(seated), 'seated_n': len(seated), 'loose': pca(loose), 'loose_n': len(loose), 'ammo': pca(ammo), 'ammo_n': len(ammo)}
# scale ratio by PCA extents (largest)
es = sorted(R['seated']['extent'], reverse=True); el = sorted(R['loose']['extent'], reverse=True); R['extent_sorted'] = [es, el]
# rigid ICP (no scale) from loose to seated, started from the PCA alignment (try the 4 sign flips)
def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0); H = (A - ca).T @ (B - cb); u, s, vt = np.linalg.svd(H); d = np.sign(np.linalg.det(vt.T @ u.T)); D = np.diag([1, 1, d]); Rm = vt.T @ D @ u.T; return Rm, cb - Rm @ ca
from mathutils import kdtree
def icp(src, dst, R0, t0, it=40):
    kd = kdtree.KDTree(len(dst))
    for i, p in enumerate(dst): kd.insert(p, i)
    kd.balance(); Rm, t = R0, t0
    for _ in range(it):
        cur = src @ Rm.T + t; nn = np.array([dst[kd.find(p)[1]] for p in cur[::3]]); Rn, tn = kabsch(src[::3], nn); Rm, t = Rn, tn
    cur = src @ Rm.T + t; res = np.sqrt(np.mean([np.sum((dst[kd.find(p)[1]] - p) ** 2) for p in cur[::5]])); return Rm, t, res
Ps, Pl = R['seated'], R['loose']; As = np.array(Ps['axes']); Al = np.array(Pl['axes']); cs = np.array(Ps['center']); cl = np.array(Pl['center'])
best = None
for sx in (1, -1):
    for sy in (1, -1):
        S = np.diag([sx, sy, sx * sy]); Rm0 = As.T @ S @ Al; t0 = cs - Rm0 @ cl
        Rm, t, res = icp(loose, seated, Rm0, t0)
        if best is None or res < best[2]: best = (Rm, t, res)
R['icp_rms'] = float(best[2]); R['icp_R'] = best[0].tolist(); R['icp_t'] = best[1].tolist()
aligned = loose @ best[0].T + best[1]; R['aligned_bbox'] = [aligned.min(0).tolist(), aligned.max(0).tolist()]; R['seated_bbox'] = [seated.min(0).tolist(), seated.max(0).tolist()]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_mag_analysis.json', 'w'), indent=1); print('MAG_ANALYSIS rms', R['icp_rms'], 'extents', es, el)
