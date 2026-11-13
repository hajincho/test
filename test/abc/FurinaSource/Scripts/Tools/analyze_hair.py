"""Compares ue_hairprobe.json (PIE, Head space) with the reference pose (Head space)."""
import json, math, sys
D = sys.argv[1]
ref = json.load(open(D + r'\ue_ref.json', encoding='utf-8'))
pl = json.load(open(D + r'\furina_player.json', encoding='utf-8'))
rows = [r for r in json.load(open(D + r'\ue_hairprobe.json')) if 'err' not in r]
parent = {}
for n in pl['nodes'].values():
    if n['path'].startswith('Furina Player/ModelRoot/Furina/Armature/'):
        p = pl['nodes'].get(n['parent'])
        parent[n['name'].replace(' ', '-')] = p['name'].replace(' ', '-') if p and p['name'] != 'Armature' else None
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3]))[:3]
G = {}
def glob(b):
    if b in G: return G[b]
    p = parent.get(b); lp = ref[b]['p']; lq = tuple(ref[b]['q'])
    if p is None: G[b] = (tuple(lp), lq)
    else:
        pp, pq = glob(p); G[b] = (tuple(a + c for a, c in zip(pp, qrot(pq, lp))), qmul(pq, lq))
    return G[b]
hp, hq = glob('Head'); hinv = (-hq[0], -hq[1], -hq[2], hq[3])
def head_space(b): return qrot(hinv, tuple(a - c for a, c in zip(glob(b)[0], hp)))
print('rows', len(rows), 'vel0', rows[0]['vel'])
for b in [k for k in rows[0] if k not in ('t', 'vel', 'Head')]:
    r = [round(x, 1) for x in head_space(b)]
    xs = [row[b] for row in rows]
    mean = [round(sum(v[i] for v in xs) / len(xs), 1) for i in range(3)]
    spread = round(max(math.dist(v, mean) for v in xs), 2)
    print('%-9s ref %-22s sim %-22s off %5.1f  jitter %5.2f' % (b, r, mean, math.dist(r, mean), spread))
