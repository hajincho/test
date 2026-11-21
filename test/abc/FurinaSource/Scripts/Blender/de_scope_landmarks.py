"""blender -b --python de_scope_landmarks.py : 소총(kar98k, g43) 길이 방향 단면 윤곽 + 조준경(zf4/zf39/zf41) 크기, ZF39 폴더의 SAMLPE.stl(마운트?) 조사 -> Data/de_scope_landmarks.json
 좌표: Blender(정리본) 총구 -Y, 위 +Z, 총의 오른쪽 = -X.  단위 cm."""
import bpy, json, glob
import numpy as np
EXP = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export'; SRC = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def load(path, fbx=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if fbx: bpy.ops.import_scene.fbx(filepath=path)
    else: bpy.ops.wm.stl_import(filepath=path)
    P = []; mats = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        M = np.array(o.matrix_world); me = o.data
        co = np.array([v.co[:] for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
        mi = np.zeros(len(co), int)
        for p in me.polygons:
            for vi in p.vertices: mi[vi] = p.material_index
        P.append(co); mats.append(mi)
    return np.vstack(P) * (100.0 if fbx else 1.0), np.concatenate(mats)
R = {}
for k in ('kar98k', 'g43'):
    P, mi = load(EXP + '\\SM_DE_%s.fbx' % k)
    ys = np.arange(np.floor(P[:, 1].min()), np.ceil(P[:, 1].max()) + 1, 1.0); prof = []
    for y in ys:
        m = (P[:, 1] >= y) & (P[:, 1] < y + 1)
        if not m.any(): continue
        Q = P[m]; prof.append([float(y), round(float(Q[:, 2].max()), 2), round(float(Q[:, 2].min()), 2), round(float(Q[:, 0].min()), 2), round(float(Q[:, 0].max()), 2), int(m.sum())])
    R[k] = {'bmin': P.min(0).round(2).tolist(), 'bmax': P.max(0).round(2).tolist(), 'profile': prof}
for k in ('zf4', 'zf39', 'zf41'):
    P, mi = load(EXP + '\\SM_DE_%s.fbx' % k); R[k] = {'bmin': P.min(0).round(2).tolist(), 'bmax': P.max(0).round(2).tolist()}
    ys = np.arange(np.floor(P[:, 1].min()), np.ceil(P[:, 1].max()) + 1, 1.0)
    R[k]['profile'] = [[float(y), round(float(P[(P[:, 1] >= y) & (P[:, 1] < y + 1), 2].max()), 2), round(float(P[(P[:, 1] >= y) & (P[:, 1] < y + 1), 2].min()), 2)] for y in ys if ((P[:, 1] >= y) & (P[:, 1] < y + 1)).any()]
for f in glob.glob(SRC + r'\zf39_scope\zf39-low-turret-mount-1.snapshot.2\*.stl'):
    P, _ = load(f, False); R['zf39_mount_stl'] = {'file': f, 'n': len(P), 'size_mm': (P.max(0) - P.min(0)).round(2).tolist()}
json.dump(R, open(D + r'\de_scope_landmarks.json', 'w'), indent=1)
print('LANDMARKS_OK')
