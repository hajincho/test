"""First-person rifle poses from the real rifle mesh (Data/rifle_geometry.json, Blender armature space -> UE: (x, -y, z)).
All poses are the gun frame (rifle origin = grip) relative to the eye point, component axes (X left, Y forward, Z up),
eye forward = +Y. Constraint: no rifle vertex inside the view frustum closer than NEAR+MARGIN (else the camera near
plane cuts the rifle open), arms must reach (Furina arm 39.2 cm). Score for the hip pose: screen area the rifle covers
(coarse grid), aiming for a template-like lower-right view. Writes the result into Data/fp_rig.json (poses block).
usage: gen_fp_poses.py <Data>"""
import json, math, sys
D = sys.argv[1]
G = json.load(open(D + r'\rifle_geometry.json'))
FR = json.load(open(D + r'\fp_rig.json'))
S = FR['scale']
V = [(x * S, -y * S, z * S) for i, (x, y, z) in enumerate(G['verts']) if i % 2 == 0]
NEAR, MARGIN = 4.0, 2.0                 # camera near clip plane lowered to 4 cm (DefaultEngine.ini NearClipPlane), 2 cm margin
FOV_H, ASPECT = 85.0, 16 / 9
SIGHT_Z, REAR_Y, FRONT_Y = 9.6 * S, -1.0 * S, 28.0 * S          # sight line in the rifle frame (cm, scaled)
SH_R, SH_L, ARM = (-10.25, -10.3, -21.0), (10.25, -10.3, -21.0), 38.0  # shoulders relative to the eye (PIE rest pose)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3]))[:3]
def qaxis(ax, deg): s = math.sin(math.radians(deg) / 2); return (ax[0] * s, ax[1] * s, ax[2] * s, math.cos(math.radians(deg) / 2))
GQ = tuple(FR['gun_q'])
def evaluate(off, q, fov=FOV_H):
    th = math.tan(math.radians(fov / 2)); tv = th / ASPECT
    cells, near_hits, mind = set(), 0, 999
    for v in V:
        p = qrot(q, v); x, y, z = off[0] + p[0], off[1] + p[1], off[2] + p[2]
        if y <= 0.5: continue
        sx, sz = -x / (y * th), z / (y * tv)              # screen: +sx right, +sz up, visible in [-1, 1]
        if abs(sx) <= 1.05 and abs(sz) <= 1.05:
            mind = min(mind, y)
            if y < NEAR + MARGIN: near_hits += 1
            if abs(sx) <= 1 and abs(sz) <= 1: cells.add((int((sx + 1) * 20), int((sz + 1) * 12)))
    rw = [o + p for o, p in zip(off, qrot(q, [t for t in FR['t_r']]))]
    lw = [o + p for o, p in zip(off, qrot(q, [t for t in FR['t_l']]))]
    reach = max(math.dist(rw, SH_R), math.dist(lw, SH_L))
    return dict(area=len(cells) / (40 * 24), near_hits=near_hits, min_depth=round(mind, 1), reach=round(reach, 1))
def ok(e): return e['near_hits'] == 0 and e['reach'] <= ARM
rep = {}
# --- current hip pose (eye anchored) as the baseline
cur = tuple(FR['g_off_eye']); rep['current_hip'] = evaluate(cur, GQ)
# --- hip: search for the most visible clip-free pose (lower right, close to the template view)
best = None
for x in range(-14, -1):
    for y in range(4, 26):
        for z in range(-18, -3):
            e = evaluate((x, y, z), GQ)
            if not ok(e): continue
            # prefer area, then keep the gun lower-right (template look), not centred
            score = e['area'] - 0.002 * abs(x + 8) - 0.002 * abs(z + 11)
            if best is None or score > best[0]: best = (score, (x, y, z), e)
rep['hip'] = dict(off=best[1], **best[2])
# --- ADS: sight line on the eye axis, rifle upright (no cant), rear sight at the closest clip-free distance
q_ads = (0.0, 0.0, 0.0, 1.0)
for relief in [x * 0.5 for x in range(16, 60)]:
    off = (0.0, relief - REAR_Y, -SIGHT_Z)
    e = evaluate(off, q_ads, fov=60.0)
    if ok(e): rep['ads'] = dict(off=off, relief=relief, **e); break
# --- shoulder (hold): stock to the shoulder, rifle aimed straight, a little right of and below the eye line
for dz in range(-3, -15, -1):
    off = (rep['ads']['off'][0] - 4.0, rep['ads']['off'][1] + 1.0, rep['ads']['off'][2] + dz)
    e = evaluate(off, GQ)
    if ok(e): rep['shoulder'] = dict(off=off, **e); break
# --- sprint: stronger cant, pulled to the chest (relative to the hip pose), must stay clip-free
SP = dict(yaw=-30.0, roll=45.0, pitch=-8.0, off=(4.0, -6.0, -8.0))
for k in range(0, 10):
    q_sp = qmul(qaxis((0, 0, 1), SP['yaw']), qmul(qaxis((0, 1, 0), SP['roll']), qaxis((1, 0, 0), SP['pitch'])))
    off = tuple(h + o for h, o in zip(rep['hip']['off'], SP['off']))
    e = evaluate(off, qmul(q_sp, GQ))
    if ok(e): break
    SP['off'] = (SP['off'][0], SP['off'][1] + 1.0, SP['off'][2])   # back off forward until clip-free
rep['sprint'] = dict(off=off, q=q_sp, delta=SP, **e)
FR['poses'] = dict(hip=list(rep['hip']['off']), shoulder=list(rep['shoulder']['off']), ads=list(rep['ads']['off']), ads_q=list(q_ads),
                   sprint_off=list(SP['off']), sprint_q=list(q_sp), ads_fov=60.0, check={k: {kk: vv for kk, vv in v.items() if kk not in ('q',)} for k, v in rep.items() if isinstance(v, dict)})
FR['poses']['check']['current_hip'] = rep['current_hip']
json.dump(FR, open(D + r'\fp_rig.json', 'w'), indent=1)
for k, v in rep.items(): print(k, {kk: vv for kk, vv in v.items() if kk != 'q'})
