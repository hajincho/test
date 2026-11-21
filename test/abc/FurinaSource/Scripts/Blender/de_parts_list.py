"""blender -b --python de_parts_list.py -- <키> [x0 x1 y0 y1 z0 z1] : 정리본 FBX 의 떨어진 덩어리(연결 성분) 목록(영역 필터, cm) -> Data/de_parts_<키>.json
 움직이는 부품(볼트, 방아쇠, 클립 등)을 찾기 위한 조사용."""
import bpy, bmesh, sys, json
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]; K = A[0]; BOX = [float(v) for v in A[1:7]] if len(A) >= 7 else None
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export\SM_DE_%s.fbx' % K)
out = []
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    M = np.array(o.matrix_world); bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    co = np.array([v.co[:] for v in bm.verts]) @ M[:3, :3].T * 100 + M[:3, 3] * 100
    seen = np.zeros(len(bm.verts), bool)
    for v in bm.verts:
        if seen[v.index]: continue
        st = [v]; comp = []; seen[v.index] = True
        while st:
            x = st.pop(); comp.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if not seen[y.index]: seen[y.index] = True; st.append(y)
        P = co[comp]; lo, hi = P.min(0), P.max(0)
        if BOX and not (lo[0] < BOX[1] and hi[0] > BOX[0] and lo[1] < BOX[3] and hi[1] > BOX[2] and lo[2] < BOX[5] and hi[2] > BOX[4]): continue
        mats = sorted({o.data.materials[f.material_index].name for vi in comp[:200] for f in bm.verts[vi].link_faces if o.data.materials})
        out.append({'obj': o.name, 'n': len(comp), 'lo': lo.round(2).tolist(), 'hi': hi.round(2).tolist(), 'mats': mats})
    bm.free()
out.sort(key=lambda e: e['lo'][1])
json.dump(out, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\de_parts_%s.json' % K, 'w'), indent=0)
print('PARTS', K, len(out))
for e in out: print('P', e['obj'], e['n'], e['lo'], e['hi'], e['mats'])
