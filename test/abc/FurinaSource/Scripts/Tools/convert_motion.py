"""Unity motion recording (FurinaMotionRecorder) -> UE local tracks for SK_Furina.
usage: convert_motion.py <Data> <idle|walk> <start> <count> <crossfade_frames>"""
import json, math, sys
D, mode, start, count, X = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rec = json.load(open(D + r'\unity_%s.json' % mode))
ue = json.load(open(D + r'\ue_ref.json', encoding='utf-8'))
pl = json.load(open(D + r'\furina_player.json', encoding='utf-8'))
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3]))[:3]
def norm(q): l = math.sqrt(sum(c*c for c in q)); return tuple(c / l for c in q)
def slerp(a, b, t):
    d = sum(x*y for x, y in zip(a, b))
    if d < 0: b = tuple(-c for c in b); d = -d
    if d > .9995: return norm(tuple(x + (y - x)*t for x, y in zip(a, b)))
    th = math.acos(d); s = math.sin(th)
    return tuple((math.sin((1-t)*th)*x + math.sin(t*th)*y)/s for x, y in zip(a, b))
names = [b.replace(' ', '-') for b in rec['bones']]
frames = rec['frames'][start:start + count]; N = len(frames)
conv = lambda q: norm((-q[0], -q[1], q[2], q[3]))
rot = [[conv(f['r'][i]) for i in range(len(names))] for f in frames]
hips = [(-f['hips'][0]*100, -f['hips'][1]*100, f['hips'][2]*100) for f in frames]
for i in range(len(names)):
    for k in range(1, N):
        if sum(a*b for a, b in zip(rot[k][i], rot[k-1][i])) < 0: rot[k][i] = tuple(-c for c in rot[k][i])
for k in range(N - X, N):   # optional loop crossfade
    t = (k - (N - X)) / X; t = t*t*(3 - 2*t)
    for i in range(len(names)): rot[k][i] = slerp(rot[k][i], rot[0][i], t)
    hips[k] = tuple(a + (b - a)*t for a, b in zip(hips[k], hips[0]))
uparent = {}
for n in pl['nodes'].values():
    if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/'):
        p = pl['nodes'].get(n['parent'])
        uparent[n['name'].replace(' ', '-')] = p['name'].replace(' ', '-') if p and p['name'] != 'Armature' else None
idx = {n: i for i, n in enumerate(names)}
def chain_to(b):
    path = [b]
    while uparent.get(path[-1]): path.append(uparent[path[-1]])
    return path[::-1]
def fk(b, k=None):
    pos = (0, 0, 0); q = (0, 0, 0, 1)
    for n in chain_to(b):
        lp = ue[n]['p']; lq = rot[k][idx[n]] if (k is not None and n in idx) else tuple(ue[n]['q'])
        if n == 'Hips': pos = tuple(hips[k] if k is not None else lp); q = lq; continue
        pos = tuple(a + c for a, c in zip(pos, qrot(q, lp))); q = qmul(q, lq)
    return pos
# vertical placement: in each frame the lowest toe/ankle should sit where it does in the reference pose
ref_low = min(fk('Left-toe')[2], fk('Right-toe')[2])
lows = [min(fk(b, k)[2] for b in ('Left-toe', 'Right-toe')) for k in range(N)]
dz = ref_low - (sorted(lows)[len(lows)//2] if mode == 'walk' else min(lows))
hips = [(h[0], h[1], h[2] + dz) for h in hips]
rep = dict(mode=mode, frames=N, dz=round(dz, 2), toe_ref=round(ref_low, 2),
           ankleZ=[[round(fk(s, k)[2], 1) for s in ('Left-ankle', 'Right-ankle')] for k in range(0, N, max(1, N//8))],
           toeZ=[[round(fk(s, k)[2], 1) for s in ('Left-toe', 'Right-toe')] for k in range(0, N, max(1, N//8))],
           headZ=round(fk('Head', 0)[2], 1), headRef=round(fk('Head')[2], 1),
           feetX=[[round(fk(s, k)[0], 1) for s in ('Left-ankle', 'Right-ankle')] for k in (0, N//2)])
json.dump(dict(fps=30, frames=N, bones=names, rot=[[list(r) for r in fr] for fr in rot], hips=[list(h) for h in hips]),
          open(D + r'\ue_%s_tracks.json' % mode, 'w', encoding='utf-8'))
print(json.dumps(rep))
