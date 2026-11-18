"""blender.exe -b --python analyze_colt_parts.py : Colt_m4A1.fbx 의 m4a1.001 본체(탄창 면 제외)를 연결 성분(좌표 일치 정점 병합)으로 나눠 크기/재질/경계를 기록 -> Data/colt_parts.json
총 길이축 = 월드 Y(길이 약 2.8 단위), 위 = Z. 노리쇠/장전손잡이 후보를 찾기 위한 분석."""
import bpy, bmesh, json
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
comps = {}
for p in me.polygons:
    r = find(key(me.vertices[p.vertices[0]])); c = comps.setdefault(r, {'faces': 0, 'mats': {}, 'min': [1e9] * 3, 'max': [-1e9] * 3, 'verts': set()})
    c['faces'] += 1; m = mats[p.material_index]; c['mats'][m] = c['mats'].get(m, 0) + 1
    for i in p.vertices:
        w = M @ me.vertices[i].co; c['verts'].add(key(me.vertices[i]))
        for k in range(3): c['min'][k] = min(c['min'][k], w[k]); c['max'][k] = max(c['max'][k], w[k])
out = []
for r, c in comps.items(): out.append({'faces': c['faces'], 'verts': len(c['verts']), 'mats': c['mats'], 'min': [round(x, 3) for x in c['min']], 'max': [round(x, 3) for x in c['max']]})
out.sort(key=lambda d: -d['faces'])
json.dump({'n': len(out), 'mats': mats, 'comps': out[:80]}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\colt_parts.json', 'w'), indent=1)
print('PARTS', len(out), [(d['faces'], d['mats']) for d in out[:12]])
