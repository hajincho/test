"""Finds hitches in the walk cycle: per-frame joint angle steps and foot/hip position steps (incl. the loop seam)."""
import json, math, sys
D = sys.argv[1]
d = json.load(open(D + r'\ue_walk_tracks.json', encoding='utf-8'))
ref = json.load(open(D + r'\ue_ref.json', encoding='utf-8'))
pl = json.load(open(D + r'\furina_player.json', encoding='utf-8'))
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3]))[:3]
def ang(a, b): return math.degrees(2 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))
par = {}
for n in pl['nodes'].values():
    if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/'):
        p = pl['nodes'].get(n['parent'])
        par[n['name'].replace(' ', '-')] = p['name'].replace(' ', '-') if p and p['name'] != 'Armature' else None
names = d['bones']; idx = {n: i for i, n in enumerate(names)}; N = d['frames']
def fk(b, k):
    path = [b]
    while par.get(path[-1]): path.append(par[path[-1]])
    pos = (0, 0, 0); q = (0, 0, 0, 1)
    for n in path[::-1]:
        lq = tuple(d['rot'][k][idx[n]]) if n in idx else tuple(ref[n]['q'])
        if n == 'Hips': pos = tuple(d['hips'][k]); q = lq; continue
        pos = tuple(a + c for a, c in zip(pos, qrot(q, ref[n]['p']))); q = qmul(q, lq)
    return pos
frames = list(range(N)) + [0]          # include the loop seam N-1 -> 0
print('frames', N, 'fps', d['fps'])
for b in ('Right-leg', 'Right-knee', 'Right-ankle', 'Right-toe', 'Left-leg', 'Left-knee', 'Left-ankle', 'Hips', 'Spine'):
    i = idx[b]
    steps = [ang(d['rot'][frames[k]][i], d['rot'][frames[k + 1]][i]) for k in range(N)]
    med = sorted(steps)[N // 2]
    worst = sorted(range(N), key=lambda k: -steps[k])[:3]
    print('%-12s median %.2f deg/frame  worst %s' % (b, med, [(k, round(steps[k], 2)) for k in worst]))
for b in ('Right-ankle', 'Left-ankle', 'Right-toe'):
    P = [fk(b, k) for k in range(N)]
    vel = [math.dist(P[frames[k]], P[frames[k + 1]]) for k in range(N)]
    acc = [abs(vel[(k + 1) % N] - vel[k]) for k in range(N)]
    worst = sorted(range(N), key=lambda k: -acc[k])[:4]
    print('%-12s pos step cm max %.2f, accel spikes %s' % (b, max(vel), [(k, round(acc[k], 2), round(vel[k], 2)) for k in worst]))
    print('   Y(fwd) per frame', [round(p[1], 1) for p in P])
    print('   Z per frame     ', [round(p[2], 1) for p in P])
hz = [h[2] for h in d['hips']]; hy = [h[1] for h in d['hips']]
print('hips Z', [round(z, 1) for z in hz])
print('hips Y', [round(y, 1) for y in hy])
