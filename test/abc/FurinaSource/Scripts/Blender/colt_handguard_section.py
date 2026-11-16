"""Blender headless: cross-sections of the Colt rifle body (FBX/M4/SK_M4A1.fbx, rifle-local cm in UE axes: Blender (x, y, z) -> UE (x, -y, z) after the FBX axis conversion; this script reads the FBX as imported
and reports in UE rifle-local) for y = 4 .. 32 cm in 2 cm steps: x / z min / max and the centroid of the vertices in the slice -> Data/colt_handguard_section.json"""
import bpy, json, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\M4\SK_M4A1.fbx')
pts = []
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        M = o.matrix_world
        for v in o.data.vertices: pts.append(M @ v.co)
# the imported FBX is Z-up, -Y forward (axis_forward='-Y'): find which axis is the barrel (longest)
ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
R = {'extent': ext, 'n': len(pts), 'slices': {}}
ax = ext.index(max(ext))
R['barrel_axis'] = ax
lo = min(p[ax] for p in pts); hi = max(p[ax] for p in pts); R['range'] = [lo, hi]
others = [i for i in range(3) if i != ax]
for k in range(-2, 18):
    c0 = lo + (k * 2 + 40) * 0.01 if False else None
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_handguard_section.json', 'w'), indent=1)
# slices in FBX/Blender units (metres): UE y (cm) = barrel coordinate relative to the muzzle end: report by distance from the muzzle end
sl = {}
for d_cm in range(0, 80, 2):
    t = (hi - d_cm * 0.01 - 0.01, hi - d_cm * 0.01 + 0.01) if True else None
    sel = [p for p in pts if lo <= p[ax] and t[0] <= p[ax] <= t[1]]
    if not sel: continue
    a = [min(p[others[0]] for p in sel), max(p[others[0]] for p in sel)]; b = [min(p[others[1]] for p in sel), max(p[others[1]] for p in sel)]
    sl[str(d_cm)] = dict(n=len(sel), u=[round(a[0] * 100, 2), round(a[1] * 100, 2)], v=[round(b[0] * 100, 2), round(b[1] * 100, 2)], axes=others)
R['by_distance_from_end_cm'] = sl
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_handguard_section.json', 'w'), indent=1); print('SECTION', ext, ax)
