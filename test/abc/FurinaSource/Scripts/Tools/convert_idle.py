"""Unity idle recording -> UE local tracks for SK_Furina (+ FK sanity check, loop crossfade, blink)."""
import json, math, sys
S = sys.argv[1]
rec = json.load(open(S + r'\unity_idle.json'))
ue = json.load(open(S + r'\ue_ref.json', encoding='utf-8'))

def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v):
    p = qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3])); return p[:3]
def norm(q):
    l = math.sqrt(sum(c*c for c in q)); return tuple(c / l for c in q)
def slerp(a, b, t):
    d = sum(x*y for x, y in zip(a, b))
    if d < 0: b = tuple(-c for c in b); d = -d
    if d > .9995: return norm(tuple(x + (y - x) * t for x, y in zip(a, b)))
    th = math.acos(d); s = math.sin(th)
    return tuple((math.sin((1-t)*th)*x + math.sin(t*th)*y) / s for x, y in zip(a, b))

names = [b.replace(' ', '-') for b in rec['bones']]
frames = rec['frames']; N = len(frames)
conv = lambda q: norm((-q[0], -q[1], q[2], q[3]))
rot = [[conv(f['r'][i]) for i in range(len(names))] for f in frames]
hips = [(-f['hips'][0]*100, -f['hips'][1]*100, f['hips'][2]*100) for f in frames]
# keep quaternion sign continuity per bone
for i in range(len(names)):
    for k in range(1, N):
        if sum(a*b for a, b in zip(rot[k][i], rot[k-1][i])) < 0: rot[k][i] = tuple(-c for c in rot[k][i])
# seamless loop: crossfade the final 0.6 s into the first frames
X = 18
for k in range(N - X, N):
    t = (k - (N - X)) / X; t = t*t*(3 - 2*t)
    j = k - (N - X)  # blend toward frame j of the start so the end meets frame 0
    for i in range(len(names)):
        rot[k][i] = slerp(rot[k][i], rot[0][i], t)
    hips[k] = tuple(a + (b - a)*t for a, b in zip(hips[k], hips[0]))

# FK check (component space) for ankles vs reference
parent = {}
idx = {n: i for i, n in enumerate(names)}
pl = json.load(open(S + r'\furina_player.json', encoding='utf-8'))
uparent = {}
for n in pl['nodes'].values():
    if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/'):
        p = pl['nodes'].get(n['parent'])
        uparent[n['name'].replace(' ', '-')] = p['name'].replace(' ', '-') if p and p['name'] != 'Armature' else None
def chain_to(b):
    path = [b]
    while uparent.get(path[-1]): path.append(uparent[path[-1]])
    return path[::-1]
def fk(b, k=None):
    pos = (0, 0, 0); q = (0, 0, 0, 1); sc = 1
    for n in chain_to(b):
        lp = ue[n]['p']; lq = tuple(ue[n]['q'])
        if k is not None and n in idx: lq = rot[k][idx[n]]
        if n == 'Hips':
            lp = hips[k] if k is not None else lp
            pos = tuple(lp); q = lq; sc = ue['Hips']['s'][0]; continue
        off = qrot(q, tuple(c*sc for c in lp)); pos = tuple(a + b for a, b in zip(pos, off)); q = qmul(q, lq)
    return pos
rep = {}
for b in ('Left-ankle', 'Right-ankle', 'Left-toe', 'Right-toe', 'Right-knee', 'Left-knee', 'Head', 'Left-wrist'):
    rep[b] = dict(ref=[round(c, 1) for c in fk(b)], idle0=[round(c, 1) for c in fk(b, 0)], idle150=[round(c, 1) for c in fk(b, 150)])
# floor match: lowest ankle in the idle equals the reference ankle height
ref_ankle = min(fk('Left-ankle')[2], fk('Right-ankle')[2])
dz = ref_ankle - min(fk('Left-ankle', 0)[2], fk('Right-ankle', 0)[2])
rep['hips_dz'] = round(dz, 2)
hips = [(h[0], h[1], h[2] + dz) for h in hips]

# --- plant both feet on flat ground (Unity recorded a slope stance): FitLeg-style two-bone IK
def qinv(q): return (-q[0], -q[1], -q[2], q[3])
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def length(a): return math.sqrt(dot(a, a))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def from_to(a, b):
    a = mul(a, 1/length(a)); b = mul(b, 1/length(b)); c = cross(a, b); d = dot(a, b)
    if d < -.99999: return (1, 0, 0, 0)
    return norm((c[0], c[1], c[2], 1 + d))
def globals_(k, bone):
    pos = (0, 0, 0); q = (0, 0, 0, 1)
    out = {}
    for n in chain_to(bone):
        lp = ue[n]['p']; lq = rot[k][idx[n]] if n in idx else tuple(ue[n]['q'])
        if n == 'Hips': pos = tuple(hips[k]); q = lq; out[n] = (pos, q); continue
        pos = add(pos, qrot(q, mul(lp, ue['Hips']['s'][0]))); q = qmul(q, lq); out[n] = (pos, q)
    return out
target_z = ref_ankle
planted = {}
for k in range(N):
    for side in ('Left', 'Right'):
        g = globals_(k, side + '-ankle')
        (H, qh), (K, qk), (A, qa) = g[side + '-leg'], g[side + '-knee'], g[side + '-ankle']
        parent_q = g[uparent[side + '-leg']][1]
        goal = (A[0], A[1], target_z)
        upper, lower = length(sub(K, H)), length(sub(A, K))
        reach = sub(goal, H); dist = min(max(length(reach), abs(upper - lower) + 1e-4), upper + lower - 1e-4)
        axis = mul(reach, 1 / length(reach))
        along = (upper*upper - lower*lower + dist*dist) / (2*dist)
        pole = sub(sub(K, H), mul(axis, dot(sub(K, H), axis)))
        newK = add(add(H, mul(axis, along)), mul(pole, math.sqrt(max(0, upper*upper - along*along)) / length(pole)))
        qh2 = qmul(from_to(sub(K, H), sub(newK, H)), qh)
        A_after = add(newK, qrot(qmul(qh2, qmul(qinv(qh), qk)), qrot(qinv(qk), sub(A, K))))
        qk_glob = qmul(qh2, qmul(qinv(qh), qk))
        qk2 = qmul(from_to(sub(A_after, newK), sub(add(H, mul(axis, dist)), newK)), qk_glob)
        # back to locals; the foot keeps its global orientation
        rot[k][idx[side + '-leg']] = norm(qmul(qinv(parent_q), qh2))
        rot[k][idx[side + '-knee']] = norm(qmul(qinv(qh2), qk2))
        rot[k][idx[side + '-ankle']] = norm(qmul(qinv(qk2), qa))
for b in ('Left-ankle', 'Right-ankle', 'Left-toe', 'Right-toe'):
    rep[b + '_planted'] = [round(c, 1) for c in fk(b, 0)]
# synthesized Unity-style blink (close .045 hold .065 open .085), at 2.9 s and 7.4 s
def blink(t):
    for s in (2.9, 7.4):
        u = t - s
        if 0 <= u < .045: x = u / .045; return 100 * x*x*(3-2*x)
        if .045 <= u < .11: return 100
        if .11 <= u < .195: x = (u - .11) / .085; return 100 * (1 - x*x*(3-2*x))
    return 0
out = dict(fps=30, frames=N, bones=names, rot=[[list(r) for r in fr] for fr in rot], hips=[list(h) for h in hips],
           blink=[blink(k/30) for k in range(N)])
json.dump(out, open(S + r'\ue_idle_tracks.json', 'w', encoding='utf-8'))
print(json.dumps(rep, indent=0))


