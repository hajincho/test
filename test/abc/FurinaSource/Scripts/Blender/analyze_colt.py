"""Blender headless: levels the Colt bore axis and reports features of m4a1.001 in the levelled frame (units as in the FBX): bore pitch, muzzle / stock centroids, per-material bounding boxes, the profile
(max / min z per y bin) and the stanag_mag faces -> Data/colt_analysis.json"""
import bpy, json, math, bmesh
from mathutils import Vector, Matrix
SRC = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_analysis.json'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=SRC)
o = bpy.data.objects['m4a1.001']; M = o.matrix_world
V = [M @ v.co for v in o.data.vertices]
ymin = min(v.y for v in V); ymax = max(v.y for v in V)
def cen(sel): return sum(sel, Vector()) / len(sel)
cm = cen([v for v in V if v.y < ymin + 0.4]); cb = cen([v for v in V if v.y > ymax - 0.25])
d = (cb - cm).normalized(); pitch = math.atan2(d.z, d.y)
R = {'pitch_deg': math.degrees(pitch), 'muzzle_centroid': tuple(cm), 'stock_centroid': tuple(cb), 'ymin': ymin, 'ymax': ymax}
Rx = Matrix.Rotation(-pitch, 4, 'X')     # level the bore (rotation about X moves z/y)
W = [Rx @ v for v in V]
R['zrange'] = [min(v.z for v in W), max(v.z for v in W)]; R['xrange'] = [min(v.x for v in W), max(v.x for v in W)]
# per material bbox (faces)
mats = [m.name if m else None for m in o.data.materials]; mb = {}
for p in o.data.polygons:
    for vi in p.vertices:
        w = W[vi]; b = mb.setdefault(mats[p.material_index], [[1e9] * 3, [-1e9] * 3])
        for k in range(3): b[0][k] = min(b[0][k], w[k]); b[1][k] = max(b[1][k], w[k])
R['material_bbox'] = {k: [[round(x, 4) for x in v[0]], [round(x, 4) for x in v[1]]] for k, v in mb.items()}
# profile
bins = {}
for w in W:
    k = round(w.y * 4) / 4; b = bins.setdefault(k, [1e9, -1e9]); b[0] = min(b[0], w.z); b[1] = max(b[1], w.z)
R['profile'] = {str(k): [round(v[0], 3), round(v[1], 3)] for k, v in sorted(bins.items())}
# rear sight material: top vertices
rs = [W[vi] for p in o.data.polygons if mats[p.material_index] == 'matech_rear_sight' for vi in p.vertices]
if rs:
    zt = max(v.z for v in rs); top = [v for v in rs if v.z > zt - 0.05]; R['rear_sight_top_centroid'] = tuple(cen(top)); R['rear_sight_centroid'] = tuple(cen(rs))
json.dump(R, open(OUT, 'w'), indent=1); print('COLT_ANALYSIS', R['pitch_deg'], R['material_bbox'])
