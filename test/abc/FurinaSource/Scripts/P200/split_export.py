"""P200 (Downloads/p200-pistol model.dae) -> 슬라이드/프레임 분리 + 실측 스케일 -> glTF 2개 (Content 임포트용).
 - 모델: x = 길이(총구 -x), y = 폭, z = 높이. 슬라이드 아랫선 z ~ 1.111, 슬라이드 후단 x ~ 1.466 (해머는 프레임 소속)
 - 스케일: 전장 196 mm (SIG P220) 기준. 피벗: 그립 위쪽 손바닥 위치(PIVOT)
 - 출력 좌표는 UE 기준(X 전방=총구, Y 오른쪽, Z 위) 으로 만든 뒤 GLTF_AXES 로 glTF 축에 대응시킨다.
사용: python split_export.py <out_dir> [axes]   axes 예) ue (기본, 그대로 기록)  /  yup (UE(x,y,z) -> glTF(-y?..))"""
import sys, os, json, base64, struct
import xml.etree.ElementTree as ET
ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
SRC = r'C:\Users\fromj\Downloads\p200-pistol\source\P200_Pistol\model\model.dae'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'L:\Saved\Scratch\p200'
AXES = sys.argv[2] if len(sys.argv) > 2 else 'ue'
SLIDE_Z, SLIDE_X = 1.105, 1.466
LEN_MM = 196.0
PIVOT = (1.00, 0.0, 0.55)   # model 좌표, 그립 중앙 위쪽
os.makedirs(OUT, exist_ok=True)
r = ET.parse(SRC).getroot(); m = r.find('.//c:geometry/c:mesh', ns)
def floats(src_id): return [float(v) for v in m.find("c:source[@id='%s']/c:float_array" % src_id, ns).text.split()]
pos = floats('meshId0-positions'); nor = floats('meshId0-normals'); uv = floats('meshId0-tex0')
pl = m.find('c:polylist', ns)
vc = [int(v) for v in pl.find('c:vcount', ns).text.split()]; p = [int(v) for v in pl.find('c:p', ns).text.split()]
tris = []; k = 0
for n in vc:
    idx = p[k:k + n]; k += n
    for j in range(1, n - 1): tris.append((idx[0], idx[j], idx[j + 1]))
xs = pos[0::3]; scale = (LEN_MM / 10.0) / (max(xs) - min(xs))   # cm per model unit
print('scale cm/unit', round(scale, 4), 'tris', len(tris))
def centroid(t): return tuple(sum(pos[3 * i + a] for i in t) / 3 for a in range(3))
parts = {'slide': [], 'frame': []}
for t in tris:
    c = centroid(t)
    parts['slide' if (c[2] > SLIDE_Z and c[0] < SLIDE_X) else 'frame'].append(t)
print({k: len(v) for k, v in parts.items()})
def to_ue(x, y, z):   # 180도 Z 회전(총구 +X) + 피벗 + 스케일 (cm)
    return (-(x - PIVOT[0]) * scale, -(y - PIVOT[1]) * scale, (z - PIVOT[2]) * scale)
def to_ue_dir(x, y, z): return (-x, -y, z)
def gl(v):   # UE(cm) -> glTF 좌표(m)
    X, Y, Z = (c / 100.0 for c in v)
    if AXES == 'ue': return (X, Y, Z)
    if AXES == 'yup': return (X, Z, Y)      # 실측: 임포트 후 UE = (gX, gZ, gY)  -> glTF = (X, Z, Y)
    raise SystemExit('axes')
def write(name, tl):
    remap = {}; P = []; N = []; T = []; I = []
    for t in tl:
        for i in t:
            if i not in remap:
                remap[i] = len(P)
                P.append(gl(to_ue(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2])))
                N.append(gl(to_ue_dir(nor[3 * i], nor[3 * i + 1], nor[3 * i + 2])))
                T.append((uv[2 * i], 1.0 - uv[2 * i + 1]))
    flip = (AXES == 'yup')   # 축 치환이 홀수 순열이 아니면 감김 유지 (아래 단순화: 그대로)
    for t in tl:   # (X,Z,Y) 치환은 반사라서 glTF 공간에서 CCW 가 되도록 감김을 뒤집는다
        I.extend([remap[t[0]], remap[t[2]], remap[t[1]]] if flip else [remap[t[0]], remap[t[1]], remap[t[2]]])
    bp = b''.join(struct.pack('<3f', *v) for v in P); bn = b''.join(struct.pack('<3f', *v) for v in N)
    bt = b''.join(struct.pack('<2f', *v) for v in T); bi = b''.join(struct.pack('<I', i) for i in I)
    buf = bp + bn + bt + bi
    mn = [min(v[a] for v in P) for a in range(3)]; mx = [max(v[a] for v in P) for a in range(3)]
    g = {'asset': {'version': '2.0', 'generator': 'p200 split'},
         'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'P200_' + name}],
         'meshes': [{'name': 'P200_' + name, 'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
         'materials': [{'name': 'M_P200_Src', 'pbrMetallicRoughness': {'baseColorFactor': [0.6, 0.6, 0.6, 1.0], 'metallicFactor': 0.0, 'roughnessFactor': 0.6}}],
         'accessors': [
             {'bufferView': 0, 'componentType': 5126, 'count': len(P), 'type': 'VEC3', 'min': mn, 'max': mx},
             {'bufferView': 1, 'componentType': 5126, 'count': len(N), 'type': 'VEC3'},
             {'bufferView': 2, 'componentType': 5126, 'count': len(T), 'type': 'VEC2'},
             {'bufferView': 3, 'componentType': 5125, 'count': len(I), 'type': 'SCALAR'}],
         'bufferViews': [
             {'buffer': 0, 'byteOffset': 0, 'byteLength': len(bp), 'target': 34962},
             {'buffer': 0, 'byteOffset': len(bp), 'byteLength': len(bn), 'target': 34962},
             {'buffer': 0, 'byteOffset': len(bp) + len(bn), 'byteLength': len(bt), 'target': 34962},
             {'buffer': 0, 'byteOffset': len(bp) + len(bn) + len(bt), 'byteLength': len(bi), 'target': 34963}],
         'buffers': [{'byteLength': len(buf), 'uri': 'data:application/octet-stream;base64,' + base64.b64encode(buf).decode()}]}
    path = os.path.join(OUT, 'P200_%s.gltf' % name); json.dump(g, open(path, 'w'))
    print(name, 'verts', len(P), 'bbox(gltf m)', [round(v, 4) for v in mn], [round(v, 4) for v in mx])
for k_, v_ in parts.items(): write(k_, v_)
