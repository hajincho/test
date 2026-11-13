import json, math, sys
s = sys.argv[1]
fbx = {m['name']: m for m in json.load(open(s + r'\fbx_nodes.json', encoding='utf-8'))['models']}
pl = json.load(open(s + r'\furina_player.json', encoding='utf-8'))
nodes = pl['nodes']

def euler_to_quat(r):  # FBX XYZ order, intrinsic as rotation matrix R = Rz*Ry*Rx
    x, y, z = [math.radians(v) for v in r]
    cx, sx, cy, sy, cz, sz = math.cos(x/2), math.sin(x/2), math.cos(y/2), math.sin(y/2), math.cos(z/2), math.sin(z/2)
    # q = qz * qy * qx
    qx = (sx, 0, 0, cx); qy = (0, sy, 0, cy); qz = (0, 0, sz, cz)
    return qmul(qz, qmul(qy, qx))

def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)

def qinv(q): return (-q[0], -q[1], -q[2], q[3])
def angle(q): return math.degrees(2 * math.acos(min(1, abs(q[3]))))

furina_ids = [t for t in pl['order'] if nodes[t]['path'].startswith('Furina Player/ModelRoot/Furina/')]
rows = []
for t in furina_ids:
    n = nodes[t]
    f = fbx.get(n['name'])
    if not f: rows.append((n['name'], 'NOT IN FBX', n['path'])); continue
    T = f['T'] or [0, 0, 0]; R = f['R'] or [0, 0, 0]; S = f['S'] or [1, 1, 1]
    fq = euler_to_quat(R); fq = (fq[0], -fq[1], -fq[2], fq[3])
    up = (-T[0], T[1], T[2])
    lp = n['lp']; lr = n['lr']; ls = n['ls']
    uq = (lr['x'], lr['y'], lr['z'], lr['w'])
    d = qmul(qinv(fq), uq)
    dp = math.dist(up, (lp['x'], lp['y'], lp['z']))
    ds = max(abs(S[0] - ls['x']), abs(S[1] - ls['y']), abs(S[2] - ls['z']))
    rows.append((n['name'], round(angle(d), 3), round(dp, 5), round(ds, 4), d))
changed = [r for r in rows if isinstance(r[1], str) or r[1] > 0.05 or r[2] > 0.0005 or r[3] > 0.001]
out = open(s + r'\compare.txt', 'w', encoding='utf-8')
print('furina nodes', len(furina_ids), 'changed', len(changed), file=out)
for r in changed: print(r[:4], file=out)
