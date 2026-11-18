"""blender.exe -b --python render_colt_parts.py : Colt 본체 연결 성분을 색으로 구분해 렌더(총 길이축 Y). 후보 성분 번호(colt_parts.json 의 comps 순서)를 색과 함께 표시.
 결과: Scratch/colt_parts_<view>_<tag>.png  (tag: all=전체, inner=큰 껍질 성분(1,4,18) 숨김)"""
import bpy, bmesh, json, math, colorsys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\colt-m4a1-carbine\source\Colt_m4A1.fbx')
src = bpy.data.objects['m4a1.001']; M = src.matrix_world; me = src.data
mats = [m.name if m else None for m in me.materials]
key = lambda v: tuple(round(c, 5) for c in (M @ v.co))
parent = {}
def find(a):
    while parent.setdefault(a, a) != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
for p in me.polygons:
    ks = [key(me.vertices[i]) for i in p.vertices]
    for k in ks[1:]: parent[find(ks[0])] = find(k)
groups = {}
for p in me.polygons:
    if mats[p.material_index] == 'stanag_mag': continue
    groups.setdefault(find(key(me.vertices[p.vertices[0]])), []).append(p.index)
order = sorted(groups.values(), key=lambda f: -len(f))
# 번호는 analyze_colt_parts.py 와 같은 정렬(면 수 내림차순, stanag_mag 포함)이라 stanag_mag 성분이 끼어 번호가 어긋날 수 있어, 여기서는 별도 번호(= 이 순서)를 쓰고 bbox 를 함께 출력
info = []
objs = []
for n, fl in enumerate(order[:70]):
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); keep = set(fl)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for v in bm.verts: v.co = M @ v.co
    m2 = bpy.data.meshes.new('c%d' % n); bm.to_mesh(m2)
    pts = [v.co for v in m2.vertices]; info.append([n, len(fl), [round(min(p[k] for p in pts), 3) for k in range(3)], [round(max(p[k] for p in pts), 3) for k in range(3)]])
    o = bpy.data.objects.new('c%d' % n, m2); bpy.context.scene.collection.objects.link(o)
    col = colorsys.hsv_to_rgb((n * 0.137) % 1.0, 0.8, 0.95) if n >= 3 else (0.6, 0.6, 0.6)
    o.color = (col[0], col[1], col[2], 1); objs.append(o)
bpy.data.objects.remove(src, do_unlink=True)
json.dump(info, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_parts_idx.json', 'w'))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 1400; sc.render.resolution_y = 500
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'; sc.display.shading.show_cavity = False
cam_d = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam; cam_d.type = 'ORTHO'; cam_d.ortho_scale = 3.4
def shoot(tag):
    for v, (loc, rot) in {'sidepx': ((10, 0.35, 1.05), (math.radians(90), 0, math.radians(90))), 'sidenx': ((-10, 0.35, 1.05), (math.radians(90), 0, math.radians(-90))), 'top': ((0, 0.35, 10), (0, 0, math.radians(90)))}.items():
        cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scratch\colt_parts_%s_%s.png' % (v, tag); bpy.ops.render.render(write_still=True)
shoot('all')
for i in (1, 4, 17, 9): objs[i].hide_render = True
shoot('inner')
import sys
HLI = [int(a) for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else [13, 65, 58, 26, 40, 55, 20, 22]
PAL = [(1, 0, 0), (0, 0.3, 1), (0, 0.8, 0), (1, 0.8, 0), (1, 0, 1), (0, 0.9, 0.9), (0.6, 0.3, 0), (0.5, 0.5, 1), (1, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.3), (0.9, 0.9, 0.9)]
HL = {n: PAL[k % len(PAL)] for k, n in enumerate(HLI)}
print('LEGEND', {n: ('#%02x%02x%02x' % tuple(int(255 * c) for c in col)) for n, col in HL.items()})
for i, o in enumerate(objs):
    o.hide_render = i not in HL and i not in (1, 4, 9, 17) is False
    if i in HL: o.color = (*HL[i], 1)
    elif i in (1, 4, 9, 17): o.hide_render = False; o.color = (0.55, 0.55, 0.55, 1)
    else: o.hide_render = True
shoot('hl')
print('RENDER_PARTS_OK')
