"""Blender headless: finds the rear aperture (the gap in the rear sight plate along the bore direction) and the front sight post of the Colt in the levelled frame
(rotation about X by -3.824 deg, same as analyze_colt.py) -> Data/colt_sights.json"""
import bpy, json, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
SRC = r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_sights.json'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=SRC)
o = bpy.data.objects['m4a1.001']; M = o.matrix_world; Rx = Matrix.Rotation(math.radians(-3.8240519141381806), 4, 'X')
V = [Rx @ (M @ v.co) for v in o.data.vertices]; F = [list(p.vertices) for p in o.data.polygons]
mats = [m.name if m else None for m in o.data.materials]
bvh = BVHTree.FromPolygons([tuple(v) for v in V], F, all_triangles=False)
R = {'scan': {}}
def hits(origin, d, lim=12):
    out = []; p = Vector(origin)
    for _ in range(lim):
        h, n, i, dist = bvh.ray_cast(p, d, 100)
        if h is None: break
        out.append((round(h.y if abs(d.y) > .5 else h.z, 4), mats[o.data.polygons[i].material_index])); p = h + d * 1e-4
    return out
for xs in (0.0,):
    for j in range(140, 200, 2):
        z = j / 100; R['scan']['x%.2f_z%.2f' % (xs, z)] = [h for h in hits((xs, -8, z), Vector((0, 1, 0))) if -3.3 < h[0] < 3.5]
# front post: top z at x=0 along y
post = []
for j in range(-300, -150, 5):
    y = j / 100; h, n, i, d = bvh.ray_cast(Vector((0, y, 3)), Vector((0, 0, -1)), 10); post.append((y, round(h.z, 4) if h else None, mats[o.data.polygons[i].material_index] if h else None))
R['post_top'] = post
# top vertices near centre in rear sight region and front region
R['rear_center_top'] = sorted([[round(v.x, 3), round(v.y, 3), round(v.z, 3)] for v in V if abs(v.x) < .12 and 0.5 < v.y < 1.1 and v.z > 1.4], key=lambda t: -t[2])[:40]
R['front_center_top'] = sorted([[round(v.x, 3), round(v.y, 3), round(v.z, 3)] for v in V if abs(v.x) < .05 and -3.0 < v.y < -2.0 and v.z > 1.45], key=lambda t: -t[2])[:30]
json.dump(R, open(OUT, 'w'), indent=1); print('COLT_SIGHTS done')
