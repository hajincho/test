"""Ballistics for the template rifle (Credit.txt: 'Low-Poly AAC Honey Badger' -> AAC Honey Badger PDW, .300 AAC Blackout).
Sources (web, 2026-11-14):
  - Wikipedia / IMFDB / Military Wiki: Honey Badger, 6 in (later 7 in) barrel, ~800 rpm cyclic, .300 BLK supersonic ~2,100 fps
    (640 m/s) from the short barrel, subsonic ~1,000 fps.
  - SIG Sauer 125 gr OTM match, G1 BC 0.338: 2,200 fps at the muzzle -> 1,759 fps at 200 yd (16 in test barrel).
  - Reviews: Q Honey Badger .300 BLK ~sub-2 MOA with match ammo.
Model used in game: v' = g - k|v|v (quadratic drag) with k fitted to the SIG velocity decay; tracer = supersonic 125 gr.
Writes Data/ballistics.json: muzzle speed, k, zero elevation for 100 m, drop table, spread and fire interval.
usage: gen_ballistics.py <Data>"""
import json, math, sys
D = sys.argv[1]
FPS = 0.3048
V0 = 2100 * FPS                                 # m/s, short barrel supersonic
K = math.log(2200 / 1759) / (200 * 0.9144)      # 1/m, from the SIG 125 gr velocity decay
G = 9.81
ZERO = 100.0                                    # m, sights zeroed at 100 m
def fly(theta, dist, dt=1e-4):
    x, y, vx, vy, t = 0.0, 0.0, V0 * math.cos(theta), V0 * math.sin(theta), 0.0
    while x < dist:
        v = math.hypot(vx, vy)
        vx += -K * v * vx * dt; vy += (-G - K * v * vy) * dt
        x += vx * dt; y += vy * dt; t += dt
    return y, t, math.hypot(vx, vy)
lo, hi = 0.0, 0.01
for _ in range(50):
    mid = (lo + hi) / 2
    if fly(mid, ZERO)[0] < 0: lo = mid
    else: hi = mid
theta = (lo + hi) / 2
lo, hi = 0.0, 0.01                              # same for the iron sights (ADS): sight line crossed at 50 m
for _ in range(50):
    mid = (lo + hi) / 2
    if fly(mid, 50.0)[0] < 0: lo = mid
    else: hi = mid
theta50 = (lo + hi) / 2
table = []
for d in (25, 50, 100, 150, 200, 250, 300, 400, 500):
    y, t, v = fly(theta, d); y0, _, _ = fly(0.0, d)
    table.append(dict(m=d, impact_cm=round(y * 100, 1), drop_flat_cm=round(y0 * 100, 1), tof_s=round(t, 3), v_ms=round(v)))
# check vs the published SIG table (100 yd zero, 200 yd: -7.5 in, from 2,200 fps) with the same model
v_keep = V0
def check():
    global V0
    V0 = 2200 * FPS; lo, hi = 0.0, 0.01
    for _ in range(50):
        mid = (lo + hi) / 2
        y = fly(mid, 91.44)[0] - 0.066 * (1 - 0)          # sight height 2.6 in: bore starts 6.6 cm below the sight line
        if fly(mid, 91.44)[0] < 0.066: lo = mid
        else: hi = mid
    y200 = fly((lo + hi) / 2, 182.88)[0] - 0.066
    V0 = v_keep
    return round(y200 / 0.0254, 1)
# ---- recoil (per shot). Weight: Q Honey Badger 7" SBR 4.5 lb (2.04 kg) -> ~2.5 kg loaded.
# impulse = bullet 8.1 g x 640 m/s + powder gas ~1.26 g x 1.75 v0  ->  ~6.6 N s, free recoil 2.6 m/s, 8.7 J (6.4 ft-lb)
# vs M4 5.56 (4 g x 900 + gas, 3.4 kg) 1.8 m/s -> 1.47x the M4's muzzle climb; game reference M4 ~0.45 deg/shot vertical
GUN_KG = 2.5
IMP = 0.0081 * V0 + 0.00126 * 1.75 * V0
M4 = (0.004 * 900 + 0.0016 * 1.75 * 900) / 3.4
RATIO = (IMP / GUN_KG) / M4
RECOIL = dict(impulse_ns=round(IMP, 2), free_recoil_ms=round(IMP / GUN_KG, 2), energy_j=round(0.5 * GUN_KG * (IMP / GUN_KG) ** 2, 1),
              ratio_vs_m4=round(RATIO, 2), vertical_deg=round(0.45 * RATIO, 3), vertical_jitter=0.15,
              horizontal_min_deg=round(-0.45 * 0.45 * RATIO, 3), horizontal_max_deg=round(0.55 * 0.45 * RATIO, 3))   # slight right drift
# ---- screen shake / recoil for a 165 cm, 22 year old woman who controls it well (2026-11-15), per shot, ADS
# Pivot model: bore 4.5 cm above the shoulder pocket -> angular impulse 6.6 N s x 0.045 m = 0.30 N m s; inertia about the shoulder
# (rifle 2.5 kg at 0.30 m + hands/forearms 1.2 kg at 0.45 m) = 0.47 kg m2 -> omega0 = 0.63 rad/s (36 deg/s). A braced, skilled shooter
# resists with ~4 Hz (omega_n = 25 rad/s): peak muzzle rise = omega0 / omega_n = 1.45 deg for the first shot. Her counter-pressure
# removes about 30 % of the accumulated climb between shots -> about 1.0 deg per shot in ADS (hip / shoulder keep the old 0.66 base).
IMP_ARM, I_SH = 0.30, 0.47
FIRST_RISE = math.degrees((IMP_ARM / I_SH) / (2 * math.pi * 4.0))
ADS_TARGET_DEG = round(FIRST_RISE * 0.7, 2)
# ---- accuracy: base cone (rifle 2 MOA + a standing shooter's hold) times the stance multiplier the user asked for
SPREAD_BASE = 0.15
STATE_MULT = dict(hip=1.10, shoulder=1.05, ads=0.90, crouch=0.90)    # crouch: x0.9 on top of the stance value (spread and recoil)
# the stance multiplier is already inside the 0.66 deg base; ADS view gain brings the final ADS climb to ADS_TARGET_DEG per shot,
# third person (FPCamera off) damps the camera kick to 30 %
RECOIL.update(first_shot_rise_deg=round(FIRST_RISE, 2), ads_vertical_deg=ADS_TARGET_DEG,
              ads_gain=round(ADS_TARGET_DEG / (RECOIL['vertical_deg'] * STATE_MULT['ads']), 2), tp_gain=0.30)
out = dict(rifle='AAC Honey Badger (.300 AAC Blackout, 125 gr supersonic tracer)', muzzle_ms=round(V0, 1), muzzle_cms=round(V0 * 100),
           k_per_m=K, k_per_cm=K / 100, zero_m=ZERO, zero_elev_rad=theta, zero50_m=50.0, zero50_elev_rad=theta50, zero_elev_deg=math.degrees(theta),
           rpm=800, interval_s=60 / 800, check_sig_200yd_in=check(), sig_published_200yd_in=-7.5,
           spread_half_deg=dict(base=SPREAD_BASE, per_cm_s=0.0015), state_mult=STATE_MULT, recoil=RECOIL, table=table)
json.dump(out, open(D + r'\ballistics.json', 'w'), indent=1)
for k, v in out.items(): print(k, v)
