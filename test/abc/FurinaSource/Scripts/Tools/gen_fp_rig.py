"""Rifle stance constants for CR_FurinaSecondary + the rifle attachment (Data/fp_rig.json), from Data/fp_measure.json.
Gun frame G (= template ik_hand_gun = rifle mesh origin) is placed relative to Furina's Neck in component axes
(Manny's FP motions distort the shoulders for the camera, so a body-relative scale of Manny's pose is not usable).
Hands: grip/handguard offsets in the gun frame come from Manny (scaled with the rifle), wrist orientations in the gun
frame come from the retargeted Furina pose (constant over every FP motion)."""
import json, math, sys
D = sys.argv[1]
m = json.load(open(D + r'\fp_measure.json'))['Idle_Loop']
SCALE = 1.0                      # real size: the mesh is the AAC Honey Badger at 1:1 (74.8 cm, real 74 cm stock extended); Furina is ~165 cm in UE
G_OFF = (-8.0, 18.0, 3.0)        # gun origin from the Neck: 8 right, 18 forward, 3 up (component axes, cm) -> visible lower right in 1st person, shouldered in 3rd
# sprint carry (PUBG-like canted low ready), applied in the gun frame with the sprint weight (CR 'Run' 0..1):
# barrel yawed 20 deg inward (left), rifle top rolled 30 deg to the left, muzzle 6 deg down; whole rifle 2 cm right, 3 cm back, 7 cm down
SPRINT_YAW, SPRINT_ROLL, SPRINT_PITCH = -20.0, 30.0, -6.0
SPRINT_OFF = (-2.0, -3.0, -7.0)
MAG = (0.0, 4.0, -9.0)           # left hand goal at the magazine well during reload (gun frame, cm before scale)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)
def qrot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0)), (-q[0], -q[1], -q[2], q[3]))[:3]
def qinv(q): return (-q[0], -q[1], -q[2], q[3])
g_q = tuple(m['manny']['gun']['q'])
t_r = [x * SCALE for x in m['hand_r_in_gun']['t']]; q_r = tuple(m['furina_rw_in_gun']['q'])
t_l = [x * SCALE for x in m['hand_l_in_gun']['t']]; q_l = tuple(m['furina_lw_in_gun']['q'])
t_mag = [x * SCALE for x in MAG]
neck = m['furina_shoulders']['neck']['t']
G = [n + o for n, o in zip(neck, G_OFF)]
rw = [a + b for a, b in zip(G, qrot(g_q, t_r))]; lw = [a + b for a, b in zip(G, qrot(g_q, t_l))]
sr, sl = m['furina_shoulders']['r']['t'], m['furina_shoulders']['l']['t']
ARM = 21.14 + 18.02
rep = dict(gun=[round(x, 1) for x in G], rw=[round(x, 1) for x in rw], lw=[round(x, 1) for x in lw],
           reach_r=round(math.dist(rw, sr), 1), reach_l=round(math.dist(lw, sl), 1), arm=ARM,
           barrel_dir=[round(x, 3) for x in qrot(g_q, (0, 1, 0))])
def qaxis(ax, deg):
    s = math.sin(math.radians(deg) / 2); return (ax[0] * s, ax[1] * s, ax[2] * s, math.cos(math.radians(deg) / 2))
# component axes: Z up (yaw), Y forward = barrel (roll), X left (pitch: +deg lifts the muzzle)
sprint_q = qmul(qaxis((0, 0, 1), SPRINT_YAW), qmul(qaxis((0, 1, 0), SPRINT_ROLL), qaxis((1, 0, 0), SPRINT_PITCH)))
Gs = [a + b for a, b in zip(G, SPRINT_OFF)]; gq_s = qmul(sprint_q, g_q)
rw_s = [a + b for a, b in zip(Gs, qrot(gq_s, t_r))]; lw_s = [a + b for a, b in zip(Gs, qrot(gq_s, t_l))]
rep.update(sprint_rw=[round(x, 1) for x in rw_s], sprint_lw=[round(x, 1) for x in lw_s], sprint_reach_r=round(math.dist(rw_s, sr), 1),
           sprint_reach_l=round(math.dist(lw_s, sl), 1), sprint_barrel=[round(x, 3) for x in qrot(gq_s, (0, 1, 0))])
# rifle component relative to Right-wrist: inverse of (rw in gun)
gun_in_rw_q = qinv(q_r)
gun_in_rw_t = qrot(gun_in_rw_q, [-x for x in t_r])
# Runtime anchor = the FP eye point (Head * CAM). Measured at rest in PIE: eye - neck = (0, 8.0, 16.6) in component axes,
# so the same standing pose is G_OFF minus that; when an animation leans the head (jump), the rifle now follows the eye.
EYE_FROM_NECK = (0.0, 8.0, 16.6)
G_OFF_EYE = tuple(round(a - b, 2) for a, b in zip(G_OFF, EYE_FROM_NECK))
CAM = (0.0, -9.0, 7.0)           # FP camera in Head bone space: 9 cm up (-Y), 7 cm forward (+Z) = eye height
out = dict(g_off_eye=G_OFF_EYE, sprint_q=sprint_q, sprint_off=SPRINT_OFF, cam_head_local=CAM, scale=SCALE, g_off=G_OFF, gun_q=g_q, t_r=t_r, q_r=q_r, t_l=t_l, q_l=q_l, t_mag=t_mag,
           gun_in_rw_t=gun_in_rw_t, gun_in_rw_q=gun_in_rw_q, check=rep)
json.dump(out, open(D + r'\fp_rig.json', 'w'), indent=1)
print(json.dumps(rep))
