import sys, json, math
sys.argv = ['x', 'Data']
src = open(r'Scripts\Tools\gen_fp_poses.py', encoding='utf-8').read().split('rep = {}')[0]
ns = {}; exec(src, ns)
ev, GQ, qmul, qaxis, qrot, V = ns['evaluate'], ns['GQ'], ns['qmul'], ns['qaxis'], ns['qrot'], ns['V']
FR = json.load(open(r'Data\fp_rig.json'))
# rifle at real size (scale 1.0, gen_fp_rig.py). Offsets = gun origin (grip) relative to the eye, component axes (X left, Y fwd, Z up)
HIP = (-7.0, 10.0, -10.0)                       # template-like lower right: 13 % of the screen, clip-free, reach 38.4 of 39.2
# ADS: sight line on the eye axis, rear sight 8 cm from the eye. PIE check at scale 0.85 (2026-11-14): rear aperture 1.8 deg
# above the dot, front post 0.35 deg above -> lowered 0.245 cm and 0.12 deg nose-up; the lowering is scaled with the rifle
ADS = (0.0, 9.0, -9.6 - 0.245 / 0.85); Q_ADS = qaxis((1, 0, 0), 0.119)
SHOULDER = (-4.0, 10.0, -11.0)                   # stock in the shoulder: straighter and closer to the eye line than hip
SP_D = (2.0, -2.0, -3.0); SP_Q = qmul(qaxis((0, 0, 1), -30), qmul(qaxis((0, 1, 0), 45), qaxis((1, 0, 0), -8)))
# third person only (no camera at the eye): the stock butt goes into the shoulder pocket instead of sticking out behind the
# back. Butt centre (rifle mesh, scale 1) = (0, -25.2, 1.3); right shoulder joint (Right-arm bone, PIE rest pose) rel. the eye =
# (-10.25, -10.3, -21). Pocket = 2 cm in front of the joint, 2.75 cm inside it, 1 cm above it. The rifle (and with it both hands,
# which are IK-ed to the rifle) moves ~8 cm forward / 11 cm down from the first-person pose. The left arm would overreach
# (44 cm vs 39 cm of arm), so the left hand slides back along the handguard (TP_LBACK) until it reaches. Faded in by the ViewTP curve.
SH_JOINT = (-10.25, -10.3, -21.0); BUTT = qrot(GQ, (0.0, -25.2, 1.3))
POCKET = (SH_JOINT[0] + 2.75, SH_JOINT[1] + 2.0, SH_JOINT[2] + 1.0)
G_TP_HIP = tuple(round(p - b, 2) for p, b in zip(POCKET, BUTT))
G_TP_SH = (G_TP_HIP[0] - 0.5, G_TP_HIP[1], G_TP_HIP[2] + 1.5)          # shouldered: a little higher and tighter against the cheek
TP_HIP_D = tuple(round(g - h, 2) for g, h in zip(G_TP_HIP, HIP))
TP_SH_D = tuple(round(g - h, 2) for g, h in zip(G_TP_SH, SHOULDER))
SH_L = (10.25, -10.3, -21.0)
LT = qrot(GQ, FR['t_l']); RT = qrot(GQ, FR['t_r'])
def lreach(g, back): return math.dist([g[i] + LT[i] + (-back if i == 1 else 0) for i in range(3)], SH_L)
TP_LBACK = 0.0
while lreach(G_TP_SH, TP_LBACK) > 37.8 or lreach(G_TP_HIP, TP_LBACK) > 37.8: TP_LBACK += 0.5
# first-person sprint sway (with the arms, phase of the 0.667 s run loop): side 1.2 cm per cycle, bob 0.8 cm per step,
# roll 3 deg / yaw 2 deg per cycle, weighted by the sprint carry weight
BOB = dict(period=0.667, side_cm=1.2, bob_cm=0.8, roll_deg=3.0, yaw_deg=2.0)
def clear(off, q=GQ): return round(min(math.dist((0, 0, 0), [o + p for o, p in zip(off, qrot(q, v))]) for v in V), 1)
chk = dict(hip=ev(HIP, GQ), shoulder=ev(SHOULDER, GQ), ads=ev(ADS, Q_ADS, fov=60.0),
           sprint=ev(tuple(a + b for a, b in zip(HIP, SP_D)), qmul(SP_Q, GQ)))
for k, v in chk.items():
    print(k, v); assert v['near_hits'] == 0 and v['reach'] <= 38.5, k
tp = dict(tp_hip=dict(gun=G_TP_HIP, reach_r=round(math.dist([G_TP_HIP[i] + RT[i] for i in range(3)], SH_JOINT), 1), reach_l=round(lreach(G_TP_HIP, TP_LBACK), 1), face_clear=clear(G_TP_HIP)),
          tp_shoulder=dict(gun=G_TP_SH, reach_r=round(math.dist([G_TP_SH[i] + RT[i] for i in range(3)], SH_JOINT), 1), reach_l=round(lreach(G_TP_SH, TP_LBACK), 1), face_clear=clear(G_TP_SH)))
for k, v in tp.items():
    print(k, v); assert max(v['reach_r'], v['reach_l']) <= 38.5 and v['face_clear'] >= 8, k
print('TP_LBACK', TP_LBACK, 'TP_HIP_D', TP_HIP_D, 'TP_SH_D', TP_SH_D)
chk.update(tp); chk['hip']['face_clear'] = clear(HIP); chk['shoulder']['face_clear'] = clear(SHOULDER)
FR['poses'] = dict(hip=HIP, shoulder=SHOULDER, ads=ADS, ads_q=Q_ADS, sprint_off=SP_D, sprint_q=SP_Q, ads_fov=60.0, hip_fov=85.0,
                   near_clip=4.0, tp_hip_d=TP_HIP_D, tp_sh_d=TP_SH_D, tp_lback=TP_LBACK, bob=BOB, check=chk)
json.dump(FR, open(r'Data\fp_rig.json', 'w'), indent=1)
print('saved')
