"""blender -b --python fx_792case.py : 7.92x57 빈 탄피(Kar98k·G43 배출용, 2026-11-23) -> FBX/FX/SM_FPVM_792Case.fbx
 치수 = mg42_assets.py 탄 단위와 같은 회전체(탄피 57mm, 림 11.95mm, 목 8.96mm), 빈 탄피라 입구 안쪽 벽(두께 0.4mm, 깊이 5mm) + 뇌관(구리, 지름 5.5mm).
 축: 탄피 머리 z 0 -> 입 z 5.7cm(+Z), 원점 = 머리(권총 SM_FPVM_9mmCase 와 같은 꼴). 재질 슬롯 Case / Primer."""
import bpy, bmesh, math, os
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'FBX', 'FX', 'SM_FPVM_792Case.fbx')
bpy.ops.wm.read_factory_settings(use_empty=True)
SEG = 24


def lathe(bm, prof, mat_index):
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / SEG) / 100, r * math.sin(2 * math.pi * k / SEG) / 100, z / 100)) for k in range(SEG)] if r > 1e-4 else [bm.verts.new((0, 0, z / 100))])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(SEG):
            f = bm.faces.new((a[0], b[k], b[(k + 1) % SEG])) if len(a) == 1 else bm.faces.new((a[k], a[(k + 1) % SEG], b[0])) if len(b) == 1 else bm.faces.new((a[k], a[(k + 1) % SEG], b[(k + 1) % SEG], b[k]))
            f.material_index = mat_index


bm = bmesh.new()
# 바깥(머리 -> 입) + 입구 안쪽 벽(입 -> 안으로 5mm) : 머리 가운데는 뇌관 둘레(r .27)에서 시작
lathe(bm, [(0.27, 0.0), (0.595, 0.0), (0.595, 0.11), (0.48, 0.14), (0.48, 0.25), (0.585, 0.30), (0.545, 4.62), (0.452, 4.98), (0.448, 5.70), (0.408, 5.70), (0.408, 5.20), (0.0, 5.20)], 0)
lathe(bm, [(0.0, -0.005), (0.27, -0.005), (0.27, 0.0)], 1)   # 뇌관(살짝 들어간 원판)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('SM_FPVM_792Case'); bm.to_mesh(me); bm.free()
for n, rgb in (('Case', (0.80, 0.60, 0.26)), ('Primer', (0.72, 0.36, 0.20))):
    m = bpy.data.materials.new(n); m.diffuse_color = (*rgb, 1); me.materials.append(m)
o = bpy.data.objects.new('SM_FPVM_792Case', me); bpy.context.scene.collection.objects.link(o)
for p in me.polygons: p.use_smooth = True
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)
print('CASE792_OK', OUT, len(me.vertices), len(me.polygons))
