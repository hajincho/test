"""Lists every object / material / connected component (loose parts) of the AR15 FBX with bounds, to find the magazine. usage: blender -b --python inspect_ar15_parts.py -- <out json>"""
import bpy, json, sys, bmesh
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\ar15\source\ar15 (2)\ar_15.fbx')
R = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH': R.append(dict(name=o.name, type=o.type)); continue
    me = o.data; M = o.matrix_world
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    # connected components
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); idx = []
        while stack:
            c = stack.pop(); idx.append(c.index)
            for e in c.link_edges:
                w = e.other_vert(c)
                if w.index not in seen: seen.add(w.index); stack.append(w)
        pts = [M @ bm.verts[i].co for i in idx]
        comps.append(dict(n=len(idx), min=[round(min(p[k] for p in pts), 3) for k in range(3)], max=[round(max(p[k] for p in pts), 3) for k in range(3)]))
    bm.free()
    comps.sort(key=lambda c: -c['n'])
    R.append(dict(name=o.name, verts=len(me.vertices), polys=len(me.polygons), materials=[m.name if m else None for m in me.materials], loc=[round(x, 3) for x in o.location], scale=[round(x, 3) for x in o.scale],
                  n_components=len(comps), components=comps[:40]))
json.dump(R, open(out, 'w'), indent=1); print('AR15_PARTS', len(R))
