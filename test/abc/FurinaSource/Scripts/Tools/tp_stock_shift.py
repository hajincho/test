"""3인칭 소총을 몸 앞쪽/바깥쪽으로 옮겨 개머리판이 몸을 뚫지 않게 한다.
사용: python tp_stock_shift.py <앞으로 cm> <오른쪽(바깥) cm> [--write]
 - 리그 축(눈 기준 컴포넌트): X=왼쪽, Y=앞, Z=위 -> 앞으로 +Y, 오른쪽(바깥) -X
 - Data/fp_rig.json poses.tp_hip_d / tp_sh_d 에 더하고, 왼팔 도달(팔 39.2cm 중 37.8) 안에 들어가도록 tp_lback 을 gen_m4_tuning.py 와 같은 식으로 다시 계산한다.
 - 기준값(원본)은 Data/fp_rig.before_stock_shift.json 에 한 번만 저장하고 항상 그 값에서 출발(여러 번 실행해도 누적되지 않음)."""
import json, math, os, sys, shutil
D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data')); P = os.path.join(D, 'fp_rig.json'); B = os.path.join(D, 'fp_rig.before_stock_shift.json')
if not os.path.exists(B): shutil.copy(P, B)
FR = json.load(open(B)); G = json.load(open(os.path.join(D, 'm4_geometry.json')))
fwd, right = float(sys.argv[1]), float(sys.argv[2]); q = FR['gun_q']
def qr(v):
    x, y, z, w = q; u = (x, y, z); dot = sum(a * b for a, b in zip(u, v)); cross = (y * v[2] - z * v[1], z * v[0] - x * v[2], x * v[1] - y * v[0])
    return [2 * dot * u[i] + (w * w - sum(a * a for a in u)) * v[i] + 2 * w * cross[i] for i in range(3)]
PO = FR['poses']; d = (-right, fwd, 0.0)
hip0 = [PO['hip'][i] + PO['tp_hip_d'][i] for i in range(3)]; sh0 = [PO['shoulder'][i] + PO['tp_sh_d'][i] for i in range(3)]
hip = [hip0[i] + d[i] for i in range(3)]; sh = [sh0[i] + d[i] for i in range(3)]
L = qr(FR['t_l']); SHL = (10.25, -10.3, -21)
def need(g0, g1):
    back = 0.0
    while max(math.dist([g[i] + L[i] - (back if i == 1 else 0) for i in range(3)], SHL) for g in (g0, g1)) > 37.8: back += .5
    return back
old_back = PO['tp_lback']; new_back = need(hip, sh); base_back = need(hip0, sh0)
print('gun hip %s -> %s ; shoulder %s -> %s' % ([round(v, 2) for v in hip0], [round(v, 2) for v in hip], [round(v, 2) for v in sh0], [round(v, 2) for v in sh]))
print('tp_lback: file %.1f, formula(old pose) %.1f, formula(new pose) %.1f -> left wrist slides back %.1f cm more (wrist gun-y 1.4 -> %.1f)' % (old_back, base_back, new_back, new_back - base_back, 1.4 - (new_back - base_back)))
out = json.load(open(B)); o = out['poses']
o['tp_hip_d'] = [round(hip[i] - PO['hip'][i], 4) for i in range(3)]; o['tp_sh_d'] = [round(sh[i] - PO['shoulder'][i], 4) for i in range(3)]; o['tp_lback'] = old_back + (new_back - base_back)   # 저장값(9.6)과 식 값(6.0)이 다르므로 늘어난 만큼만 더한다
print('tp_hip_d', o['tp_hip_d'], 'tp_sh_d', o['tp_sh_d'], 'tp_lback', o['tp_lback'])
if '--write' in sys.argv: json.dump(out, open(P, 'w'), indent=1); print('written', P)
