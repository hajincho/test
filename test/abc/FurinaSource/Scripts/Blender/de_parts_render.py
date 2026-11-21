"""blender -b --python de_parts_render.py -- <키> <y0> <y1> [H] [ZC] : 떨어진 덩어리마다 다른 색으로 칠해 옆(오른쪽/왼쪽)/위 정사영 렌더 + 번호표 -> Data/de_partsr_<키>_<view>.png, Data/de_partsr_<키>.json
 (부품 찾기용: 볼트 캐리어, 장전 손잡이, 탄창 등). 좌표 원본 cm, 총구 -Y."""
import bpy, bmesh, sys, json, math, colorsys
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]; K, Y0, Y1 = A[0], float(A[1]), float(A[2]); H = float(A[3]) if len(A) > 3 else 16.0; ZC = float(A[4]) if len(A) > 4 else 4.0
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export\SM_DE_%s.fbx' % K)
o = [x for x in bpy.data.objects if x.type == 'MESH'][0]; bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.data.transform(__import__('mathutils').Matrix.Scale(100, 4))
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lab = [-1] * len(bm.verts); comps = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = len(comps); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if lab[y.index] < 0: lab[y.index] = len(comps); st.append(y)
    comps.append(idx)
co = np.array([v.co[:] for v in bm.verts]); info = []; mats = []
for ci, idx in enumerate(comps):
    P = co[idx]; lo, hi = P.min(0), P.max(0)
    inside = lo[1] < Y1 and hi[1] > Y0 and len(idx) >= 20
    info.append({'id': ci, 'n': len(idx), 'lo': lo.round(2).tolist(), 'hi': hi.round(2).tolist(), 'shown': bool(inside)})
    m = bpy.data.materials.new('C%d' % ci); h = (ci * 0.618) % 1.0; m.diffuse_color = (*colorsys.hsv_to_rgb(h, 0.75, 0.95), 1) if inside else (0.25, 0.25, 0.25, 1); mats.append(m); o.data.materials.append(m)
for f in bm.faces: f.material_index = lab[f.verts[0].index]
bm.to_mesh(o.data); bm.free()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
W = Y1 - Y0; yc = (Y0 + Y1) / 2
for nm, loc, rot in (('right', (-60, yc, ZC), (90, 0, -90)), ('left', (60, yc, ZC), (90, 0, 90)), ('top', (0, yc, 60), (0, 0, 90))):
    sc.render.resolution_x, sc.render.resolution_y = int(W * 40), int(H * 40); cd.ortho_scale = W; cd.clip_end = 500
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    sc.render.filepath = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\de_partsr_%s_%s.png' % (K, nm); bpy.ops.render.render(write_still=True)
json.dump([i for i in info if i['shown']], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\de_partsr_%s.json' % K, 'w'), indent=0)
print('PARTSR_OK', sum(i['shown'] for i in info))
