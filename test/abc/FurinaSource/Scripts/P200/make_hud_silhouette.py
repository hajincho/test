"""P220 HUD 실루엣 PNG (1600x417, 흰색 + 알파) 생성: model.dae 를 옆면에서 채워 그린다. M4 실루엣(T_M4HUDSilhouette)과 같은 규격."""
import xml.etree.ElementTree as ET, zlib, struct, sys
ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
SRC = r'C:\Users\fromj\Downloads\p200-pistol\source\P200_Pistol\model\model.dae'
OUT = sys.argv[1] if len(sys.argv) > 1 else r'L:\Saved\Scratch\P220HUD_Silhouette.png'
W, H = 1600, 417; SS = 2                       # 2배 슈퍼샘플
r = ET.parse(SRC).getroot(); m = r.find('.//c:geometry/c:mesh', ns)
pos = [float(x) for x in m.find('c:source/c:float_array', ns).text.split()]
P = [(pos[i], pos[i + 1], pos[i + 2]) for i in range(0, len(pos), 3)]
pl = m.find('c:polylist', ns); vc = [int(x) for x in pl.find('c:vcount', ns).text.split()]; p = [int(x) for x in pl.find('c:p', ns).text.split()]
tris = []; k = 0
for n in vc:
    idx = p[k:k + n]; k += n
    for j in range(1, n - 1): tris.append((idx[0], idx[j], idx[j + 1]))
xs = [q[0] for q in P]; zs = [q[2] for q in P]; x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
Wd, Hd = W * SS, H * SS
sc = (Hd * 0.86) / (z1 - z0)                   # 높이의 86%
ox = (Wd - (x1 - x0) * sc) / 2; oy = (Hd - (z1 - z0) * sc) / 2
def proj(q): return (ox + (q[0] - x0) * sc, Hd - oy - (q[2] - z0) * sc)   # 총구 왼쪽(-x), 위 +z
mask = bytearray(Wd * Hd)
def fill(a, b, c):
    minx = max(0, int(min(a[0], b[0], c[0]))); maxx = min(Wd - 1, int(max(a[0], b[0], c[0]) + 1))
    miny = max(0, int(min(a[1], b[1], c[1]))); maxy = min(Hd - 1, int(max(a[1], b[1], c[1]) + 1))
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9: return
    for y in range(miny, maxy + 1):
        base = y * Wd
        for x in range(minx, maxx + 1):
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
            if l1 >= -0.01 and l2 >= -0.01 and 1 - l1 - l2 >= -0.01: mask[base + x] = 1
for t in tris: fill(proj(P[t[0]]), proj(P[t[1]]), proj(P[t[2]]))
rows = []
for y in range(H):
    row = bytearray(b'\x00')
    for x in range(W):
        s = 0
        for dy in range(SS):
            o = (y * SS + dy) * Wd + x * SS
            for dx in range(SS): s += mask[o + dx]
        row += bytes((255, 255, 255, int(255 * s / (SS * SS))))
    rows.append(bytes(row))
def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows), 6)) + chunk(b'IEND', b'')
open(OUT, 'wb').write(png); print('wrote', OUT, 'pistol px', round((x1 - x0) * sc / SS), 'x', round((z1 - z0) * sc / SS))
