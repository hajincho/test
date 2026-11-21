"""blender -b --python fx_smoke_puffs.py : 총구 연기 잔상용 덩어리 메시(2026-11-21) -> FBX/FX/SM_HistSmokePuffs.fbx
 공 9개(반지름 1cm, 모두 원점 중심). 재질 M_HistSmoke 가 정점색으로 덩어리마다 다르게 움직임:
   R = 무작위 씨앗, G = 총구에서 앞으로 나가는 비율(0 총구 ~ 1 가장 멀리), B = 크기 비율
 실제 위치·크기·떠오름·퍼짐·옅어짐은 재질 WPO/불투명도에서 시간(생성 후 경과)으로 계산."""
import bpy, bmesh, random, os
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('SM_HistSmokePuffs'); bm = bmesh.new()
col = bm.loops.layers.color.new('Col')
N = 9
for i in range(N):
    g = i / (N - 1); r = random.random(); b = 0.55 + 0.45 * random.random()
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.01)
    faces = set(f for v in res['verts'] for f in v.link_faces)
    for f in faces:
        for lp in f.loops: lp[col] = (r, g, b, 1.0)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
ob = bpy.data.objects.new('SM_HistSmokePuffs', me); bpy.context.scene.collection.objects.link(ob)
out = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\FX'; os.makedirs(out, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.fbx(filepath=os.path.join(out, 'SM_HistSmokePuffs.fbx'), use_selection=True, object_types={'MESH'}, colors_type='LINEAR', mesh_smooth_type='FACE', apply_unit_scale=True)
print('SMOKE_PUFFS', len(me.vertices))
