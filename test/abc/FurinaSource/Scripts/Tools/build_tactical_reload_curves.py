"""전술(탄창이 남은) 재장전 곡선 -> Data/tactical_reload_curves.json
 AS_Furina_FP_Reload(길이 3.1333초, 기존 재장전 3.0초)의 0~2.4초는 기존 곡선(reload_curves_new.json: 탄창 쥠 0.74 / 낙하 1.04 / 허리춤 새 탄창 1.39 / 장착 2.37)을 그대로 두고,
 2.4~3.1333초(22프레임)에 긴급 재장전과 같은 장전손잡이 당기기(empty_reload_curves.json 의 k37~60)를 시간만 0.955배로 줄여 넣는다. 기존의 '핸드가드로 복귀'(2.4~3.0)는 손잡이 구간 끝의 복귀로 대체된다.
 이어 붙임: t=2.4 에서 기존 곡선의 변위와 긴급 재장전의 장착 자세 변위의 차이를 손잡이를 잡는 자세(k45)까지 서서히 없앤다.
 BoltBack 은 손잡이와 같이 움직인다(노리쇠가 손잡이를 따라 7cm 뒤로, 놓으면 같이 앞으로).  재생 속도 0.85 로 재생하면 총 3.69초 (BP 쪽)."""
import json, os
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
old = json.load(open(os.path.join(D, 'reload_curves_new.json'))); emp = json.load(open(os.path.join(D, 'empty_reload_curves.json')))
T0 = 2.4; T1 = 3.13333; FPS = 30.0
def interp(ts, vs, t):
    if t <= ts[0]: return vs[0]
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]:
            u = (t - ts[i]) / (ts[i + 1] - ts[i]) if ts[i + 1] > ts[i] else 0.0; return vs[i] + (vs[i + 1] - vs[i]) * u
    return vs[-1]
def smooth(a, b, x): u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
et = emp['times']; EK = lambda t_k: t_k   # k -> 초: k/30
dold = [interp(old['times'], old[k], T0) for k in ('LX', 'LY', 'LZ')]
demp = [emp[k][37] for k in ('LX', 'LY', 'LZ')]
diff = [dold[i] - demp[i] for i in range(3)]
times = [t for t in old['times'] if t < T0 - 1e-6] + [T0]
LX = [interp(old['times'], old['LX'], t) for t in times]; LY = [interp(old['times'], old['LY'], t) for t in times]; LZ = [interp(old['times'], old['LZ'], t) for t in times]
hand = []; bolt = []; hfp = []
n = int(round((T1 - T0) * FPS))           # 22
for j in range(1, n + 1):
    t = round(T0 + j / FPS, 5); kk = 37.0 + (j / FPS) / (T1 - T0) * (60 - 37)     # 연속 k (37 -> 60)
    k0 = int(kk); k1 = min(60, k0 + 1); u = kk - k0
    g = lambda arr: arr[k0] + (arr[k1] - arr[k0]) * u
    fade = 1.0 - smooth(37, 45, kk)
    times.append(t); LX.append(g(emp['LX']) + diff[0] * fade); LY.append(g(emp['LY']) + diff[1] * fade); LZ.append(g(emp['LZ']) + diff[2] * fade)
    hv = g([v for _, v in emp['handleback']]); hand.append([t, round(hv, 4)]); bolt.append([t, round(hv, 4)])
    hfp.append([t, round(g([v for _, v in emp['handlefp']]), 4)])
LX = [round(v, 4) for v in LX]; LY = [round(v, 4) for v in LY]; LZ = [round(v, 4) for v in LZ]
handle = [[0.0, 0.0], [T0, 0.0]] + hand; boltb = [[0.0, 0.0], [T0, 0.0]] + bolt; handlefp = [[0.0, 0.0], [T0 - 0.05, 0.0]] + hfp
rifle = [[0.0, 0.0], [0.35, 1.0], [T1 - 0.08, 1.0], [T1, 0.0]]
out = {'times': times, 'LX': LX, 'LY': LY, 'LZ': LZ, 'magstate': old['magstate'], 'handleback': handle, 'boltback': boltb, 'handlefp': handlefp, 'riflereload': rifle, 'length': T1,
       'seat_old_delta': dold, 'seat_empty_delta': demp, 'diff': diff, 'rate': 0.85, 'real_seconds': round(T1 / 0.85, 3)}
json.dump(out, open(os.path.join(D, 'tactical_reload_curves.json'), 'w'), indent=1)
print('TACTICAL_CURVES keys', len(times), 'old seat delta', [round(v, 1) for v in dold], 'empty seat delta', [round(v, 1) for v in demp], 'real_seconds', out['real_seconds'])
print('end delta', LX[-1], LY[-1], LZ[-1], 'handle peak', max(v for _, v in handle))
