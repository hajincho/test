"""PMX 2.0/2.1 읽기(순수 파이썬 + numpy, Blender 안팎 공용). Blender 5.x 에 MMD 가져오기가 없어서 직접 읽는다.
read_pmx(path) -> dict(name, verts[N,3], normals[N,3], uvs[N,2], weights: list[(bone_idx, w)...], faces[M,3](PMX 원래 감김),
 textures[str], materials[dict(name, name_en, diffuse, tex, face_count, flags)], bones[dict(name, name_en, pos, parent, tail_idx, tail_off, flags)])
좌표는 PMX 그대로(왼손, Y 위, 모델은 -Z 를 봄). Blender 로는 (x, z, y) + 면 감김 뒤집기."""
import struct
import numpy as np


class _R:
    def __init__(self, b): self.b = b; self.o = 0
    def take(self, n): v = self.b[self.o:self.o + n]; self.o += n; return v
    def i8(self): return struct.unpack_from('<b', self.take(1))[0]
    def u8(self): return self.take(1)[0]
    def u16(self): return struct.unpack_from('<H', self.take(2))[0]
    def i32(self): return struct.unpack_from('<i', self.take(4))[0]
    def f(self, n=1):
        v = struct.unpack_from('<%df' % n, self.take(4 * n)); return v[0] if n == 1 else v
    def idx(self, size, signed=True):
        if size == 1: return self.i8() if signed else self.u8()
        if size == 2: return struct.unpack_from('<h' if signed else '<H', self.take(2))[0]
        return self.i32()


def read_pmx(path):
    r = _R(open(path, 'rb').read())
    assert r.take(4) == b'PMX ', 'not PMX'
    ver = r.f(); n = r.u8(); g = list(r.take(n))
    enc = 'utf-16-le' if g[0] == 0 else 'utf-8'; add_uv, vsz, tsz, msz, bsz, msz2, rsz = g[1:8]
    def text(): ln = r.i32(); return r.take(ln).decode(enc, errors='replace')
    out = {'version': ver, 'name': text(), 'name_en': text()}; text(); text()
    nv = r.i32(); V = np.zeros((nv, 3), np.float32); N = np.zeros((nv, 3), np.float32); UV = np.zeros((nv, 2), np.float32); W = []
    for i in range(nv):
        V[i] = r.f(3); N[i] = r.f(3); UV[i] = r.f(2)
        for _ in range(add_uv): r.f(4)
        t = r.u8()
        if t == 0: W.append([(r.idx(bsz), 1.0)])
        elif t == 1:
            a, b = r.idx(bsz), r.idx(bsz); w = r.f(); W.append([(a, w), (b, 1.0 - w)])
        elif t in (2, 4):
            ids = [r.idx(bsz) for _ in range(4)]; ws = r.f(4); W.append([(a, w) for a, w in zip(ids, ws) if a >= 0 and w > 0])
        elif t == 3:
            a, b = r.idx(bsz), r.idx(bsz); w = r.f(); r.f(9); W.append([(a, w), (b, 1.0 - w)])
        else: raise ValueError('weight type %d' % t)
        r.f()   # edge scale
    nf = r.i32(); F = np.array([r.idx(vsz, signed=(vsz == 4)) for _ in range(nf)], np.int64).reshape(-1, 3)
    nt = r.i32(); T = [text().replace('\\', '/') for _ in range(nt)]
    nm = r.i32(); M = []
    for _ in range(nm):
        m = {'name': text(), 'name_en': text(), 'diffuse': r.f(4)}; r.f(3); r.f(); r.f(3); m['flags'] = r.u8(); r.f(4); r.f()
        m['tex'] = r.idx(tsz); r.idx(tsz); r.u8(); shared = r.u8()
        if shared == 0: r.idx(tsz)
        else: r.u8()
        text(); m['face_count'] = r.i32() // 3; M.append(m)
    nb = r.i32(); B = []
    for _ in range(nb):
        b = {'name': text(), 'name_en': text(), 'pos': r.f(3), 'parent': r.idx(bsz)}; r.i32(); fl = r.u16(); b['flags'] = fl
        if fl & 0x1: b['tail_idx'] = r.idx(bsz); b['tail_off'] = None
        else: b['tail_off'] = r.f(3); b['tail_idx'] = -1
        if fl & 0x300: r.idx(bsz); r.f()
        if fl & 0x400: r.f(3)
        if fl & 0x800: r.f(3); r.f(3)
        if fl & 0x2000: r.i32()
        if fl & 0x20:
            r.idx(bsz); r.i32(); r.f()
            for _ in range(r.i32()):
                r.idx(bsz)
                if r.u8(): r.f(3); r.f(3)
        B.append(b)
    out.update(verts=V, normals=N, uvs=UV, weights=W, faces=F, textures=T, materials=M, bones=B, rigid=[], joints=[])
    try:   # 모프·표시 틀(건너뜀) -> 강체·조인트(물리 뼈 찾기용)
        for _ in range(r.i32()):
            text(); text(); r.u8(); t = r.u8(); n = r.i32()
            for _ in range(n):
                if t == 0: r.idx(msz2); r.f()                     # group
                elif t == 1: r.idx(vsz, signed=(vsz == 4)); r.f(3)   # vertex
                elif t == 2: r.idx(bsz); r.f(3); r.f(4)           # bone
                elif t in (3, 4, 5, 6, 7): r.idx(vsz, signed=(vsz == 4)); r.f(4)   # uv
                elif t == 8: r.idx(msz); r.u8(); r.f(4); r.f(3); r.f(); r.f(3); r.f(4); r.f(); r.f(4); r.f(4); r.f(4)   # material
                elif t == 9: r.idx(msz2); r.f()                   # flip
                elif t == 10: r.idx(rsz); r.u8(); r.f(3); r.f(3)  # impulse
                else: raise ValueError('morph type %d' % t)
        for _ in range(r.i32()):
            text(); text(); r.u8()
            for _ in range(r.i32()):
                if r.u8() == 0: r.idx(bsz)
                else: r.idx(msz2)
        RB = []
        for _ in range(r.i32()):
            rb = {'name': text()}; text(); rb['bone'] = r.idx(bsz); r.u8(); r.u16(); rb['shape'] = r.u8(); rb['size'] = r.f(3); rb['pos'] = r.f(3); rb['rot'] = r.f(3)
            rb['mass'], rb['lin_damp'], rb['ang_damp'], rb['restitution'], rb['friction'] = r.f(5); rb['mode'] = r.u8(); RB.append(rb)
        JT = []
        for _ in range(r.i32()):
            j = {'name': text()}; text(); r.u8(); j['a'] = r.idx(rsz); j['b'] = r.idx(rsz); j['pos'] = r.f(3); j['rot'] = r.f(3)
            j['lin_min'] = r.f(3); j['lin_max'] = r.f(3); j['ang_min'] = r.f(3); j['ang_max'] = r.f(3); j['spring_lin'] = r.f(3); j['spring_ang'] = r.f(3); JT.append(j)
        out['rigid'] = RB; out['joints'] = JT
    except Exception as e:
        out['rigid_error'] = str(e)[:200]
    return out


if __name__ == '__main__':
    import sys, json
    d = read_pmx(sys.argv[1])
    print(json.dumps({'name': d['name'], 'verts': len(d['verts']), 'faces': len(d['faces']), 'y': [float(d['verts'][:, 1].min()), float(d['verts'][:, 1].max())],
                      'materials': [(m['name'], d['textures'][m['tex']] if 0 <= m['tex'] < len(d['textures']) else None, m['face_count']) for m in d['materials']],
                      'bones': [b['name'] for b in d['bones']][:400]}, ensure_ascii=False))
