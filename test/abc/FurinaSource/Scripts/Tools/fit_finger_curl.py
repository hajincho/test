"""Fits the first-person left-hand finger pose (2026-11-16) so that the four fingers WRAP around the round Colt handguard.
Measured (ue_finger_probe.py, ADS state, Data/finger_probe.json): the finger bases (knuckles) already lie around the handguard circumference, but the fingers are stretched forward along the barrel and their
joints 2 / 3 run through the handguard (distance from its axis 1.2-2.4 cm < radius 2.84 cm). Handguard (Data/colt_handguard_section.json): round, axis along rifle y, centre x 0 / z 3.55, radius 2.84 cm (y 5..19 cm).
Target: each finger follows the circle of radius R_T = 2.84 + 0.6 (finger radius) around that axis in the plane of its base (constant y), starting at its base angle and going on downward / to the right
(decreasing angle in the x-z plane: left side -> underneath -> right side), joint 2 one proximal-phalanx length (chord) further, joint 3 one middle-phalanx length further, the tip 0.8 of that.
For every bone the world swing that turns its (already rotated by the parents) bone direction onto the target direction is converted to a bone-LOCAL axis / angle:  local_new = local_anim * Rot(axis_local, angle)
(Control Rig RigUnit_AddBoneTransform, post multiply).  Output Data/finger_curl.json ; with --write also fp_rig.json['fingers_l'] = {bone: {axis: [x,y,z], deg: angle}}."""
import json, math, os, sys
D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data'))
P = json.load(open(os.path.join(D, 'finger_probe.json')))['ads']
CX, CZ, RH = 0.0, 3.55, 2.84
R_T = RH + 0.6
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): n = math.sqrt(dot(a, a)); return mul(a, 1 / n) if n > 1e-9 else a
def length(a): return math.sqrt(dot(a, a))
def rodrigues(v, axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    return add(add(mul(v, c), mul(cross(axis, v), s)), mul(axis, dot(axis, v) * (1 - c)))
def swing(a, b):                          # axis, angle of the shortest rotation a -> b
    a, b = norm(a), norm(b); ax = cross(a, b); s = length(ax); c = dot(a, b)
    if s < 1e-8: return (1.0, 0.0, 0.0), (0.0 if c > 0 else math.pi)
    return mul(ax, 1 / s), math.atan2(s, c)
def on_circle(ang, y): return (CX + R_T * math.cos(ang), y, CZ + R_T * math.sin(ang))
RES = {}; OUT = {}
for name in ('Index', 'Middle', 'Ring', 'Little'):
    b = [P['%sFinger%d_L' % (name, i)] for i in (1, 2, 3)]; pos = [tuple(x['pos']) for x in b]
    tip = add(pos[2], mul(sub(pos[2], pos[1]), 0.8)); pts = pos + [tip]
    L = [length(sub(pts[i + 1], pts[i])) for i in range(3)]
    y0 = pos[0][1]; a0 = math.atan2(pos[0][2] - CZ, pos[0][0] - CX)         # base angle around the handguard axis
    tgt = [on_circle(a0, y0)]; ang = a0
    for l in L:
        ang -= 2 * math.asin(min(0.99, l / (2 * R_T))); tgt.append(on_circle(ang, y0))       # decreasing angle: left -> bottom -> right
    # the base joint itself stays where the hand puts it
    tgt[0] = pos[0]
    # sequential swings (world), accumulated rotation of the subtree = (axis list)
    cur = list(pts)          # current (after parents) positions of joints / tip
    swings = []; bones = {}
    for i in range(3):
        d_cur = sub(cur[i + 1], cur[i]); d_tgt = sub(tgt[i + 1], tgt[i])
        ax, an = swing(d_cur, d_tgt); swings.append((ax, an, cur[i]))
        # apply this swing to joint i+1 .. tip about joint i
        for k in range(i + 1, 4): cur[k] = add(cur[i], rodrigues(sub(cur[k], cur[i]), ax, an))
        # bone local axis: the bone's original world axes R0 (columns) after the cumulative rotation of the parents -> world axis ax expressed in the ORIGINAL bone frame
        # (parents' rotations are undone by applying them inversely to the axis)
        a_w = ax
        for (pax, pan, _) in reversed(swings[:-1]): a_w = rodrigues(a_w, pax, -pan)
        R = b[i]['axes']; a_local = (dot(a_w, R[0]), dot(a_w, R[1]), dot(a_w, R[2]))
        bones['%sFinger%d_L' % (name, i + 1)] = dict(axis=[round(x, 5) for x in a_local], deg=round(math.degrees(an), 3))
    RES[name] = dict(lengths=[round(l, 2) for l in L], base_angle_deg=round(math.degrees(a0), 1), target=[[round(x, 2) for x in p] for p in tgt], predicted=[[round(x, 2) for x in p] for p in cur],
                     dist_before=[round(math.hypot(p[0] - CX, p[2] - CZ), 2) for p in pts[1:]], dist_after=[round(math.hypot(p[0] - CX, p[2] - CZ), 2) for p in cur[1:]], bones=bones)
    OUT.update(bones)
json.dump(dict(radius=R_T, result=RES), open(os.path.join(D, 'finger_curl.json'), 'w'), indent=1)
for k, v in RES.items(): print(k, 'dist from axis before', v['dist_before'], 'after', v['dist_after'], 'deg', [b['deg'] for b in v['bones'].values()])
if '--write' in sys.argv:
    fr = json.load(open(os.path.join(D, 'fp_rig.json'), encoding='utf-8')); fr['fingers_l'] = OUT
    json.dump(fr, open(os.path.join(D, 'fp_rig.json'), 'w'), indent=1, ensure_ascii=False); print('fp_rig.json fingers_l written')
