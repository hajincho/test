"""긴급(빈 탄창) 재장전 곡선 v2 -> Data/empty_reload_curves.json  (v1 = build_empty_reload_curves.py: 노리쇠 멈치로 풀던 방식)
v2: 탄창을 끼운 뒤 왼손이 피카티니(상부) 뒤쪽 장전손잡이 래치를 잡아 뒤로 당겼다 놓는다(원본 FBX 의 장전손잡이 구간 f105~132 의 타이밍을 따름).
 k = 0~36 (원본 f9~45): v1 과 같음 (탄창 뽑기/교체/삽입).  MagState: 쥠 k14, 낙하 k22, 새 탄창 k25, 장착 k37.
 k = 37~45: 장착 자세 -> 장전손잡이 잡는 자세 W_G.  경로 모양은 원본 f105~115 의 왼손목 경로(직선에서 벗어나는 곡선 성분)를 따름.
 k = 45~47 당김(HandleBack 0 -> 1, 손은 5.9cm 뒤로) / 47~51 유지 / 52 놓음(손잡이 1 -> 0.4, 노리쇠 BoltBack 1 -> 0.35) / 53 완전히 앞(0, 0) / 53~60 손이 기본 위치로 복귀.
 목표 손목 위치(총 좌표 X왼쪽 Y앞 Z위 cm): W_G = (6.5, -22.3, 4.9) (검지 끝이 래치(SM_M4Handle 뒤쪽 끝 (0, -15.7, 5.5)) 왼쪽 윗면 (2.5, -15.0, 7.0)에 오도록: 측정 검지 끝 = 손목 + (-4.0, +7.3, +2.1)), 당김 W_P = W_G + (0, -5.9, 0).
 변위 = 목표 - OFF,  OFF = (-1.91, 9.83, 4.28)  (PIE 측정: 손목 = 곡선 변위 x 약 1.0 + OFF, lyra_empty_reload_probe_side.json 과 v1 곡선의 최소제곱, rms 0.14~0.40cm)"""
import json, math, os
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SC = 0.973; F0 = 9; FPS = 30.0; N = 60
OFF = (-1.91, 9.83, 4.28)
W_G = (6.5, -22.3, 4.9); PULL = 5.9
rows = {}
for fn in ('carbine_anim_f0.json', 'carbine_anim_f1.json', 'carbine_anim_f2.json', 'carbine_anim_f3.json'):
    for r in json.load(open(os.path.join(D, fn)))['samples']: rows[r['f']] = r
L = lambda f: rows[f]['L_wrist']          # [옆(+왼), 위, 앞]
old = json.load(open(os.path.join(D, 'reload_curves_new.json')))
def old_at(t, key):
    ts = old['times']; vs = old[key]
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]: return vs[i] + (vs[i + 1] - vs[i]) * (t - ts[i]) / (ts[i + 1] - ts[i])
    return vs[-1]
D_GRAB = [old_at(0.80, 'LX'), old_at(0.80, 'LY'), old_at(0.80, 'LZ')]
def smooth(a, b, x): u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
def delta_v1(f):
    l, l0 = L(f), L(F0); return [(l[0] - l0[0]) * SC, (l[2] - l0[2]) * SC, (l[1] - l0[1]) * SC]
dg = delta_v1(23); CORR = [D_GRAB[i] - dg[i] for i in range(3)]
def d_first(k):                                   # k <= 37: v1 과 같은 식 (f = 9 + k)
    f = F0 + k; w = smooth(9, 22, f); d = delta_v1(f); return [d[i] + w * CORR[i] for i in range(3)]
dl = []
for k in range(0, 38): dl.append(d_first(k))
W_seat = [dl[37][i] + OFF[i] for i in range(3)]
# 37~45: 장착 -> W_G (원본 f105~115 의 손목 경로 모양)
A, B = L(105), L(115); Dv = [B[i] - A[i] for i in range(3)]; DD = sum(x * x for x in Dv)
def path(k):
    f = 105 + (k - 37) * 1.25; l = L(int(round(f)))
    s = max(0.0, min(1.0, sum((l[i] - A[i]) * Dv[i] for i in range(3)) / DD))
    arc = [(l[i] - (A[i] + s * Dv[i])) * SC for i in range(3)]                 # [옆, 위, 앞]
    ease = s * s * (3 - 2 * s) if False else s
    return [W_seat[0] + ease * (W_G[0] - W_seat[0]) + arc[0], W_seat[1] + ease * (W_G[1] - W_seat[1]) + arc[2], W_seat[2] + ease * (W_G[2] - W_seat[2]) + arc[1]]
HK = {44: 0.0, 45: 0.0, 46: 0.55, 47: 1.0, 48: 1.0, 49: 1.0, 50: 1.0, 51: 1.0, 52: 0.4, 53: 0.0}
BK = {51: 1.0, 52: 0.35, 53: 0.0}
dG = [W_G[i] - OFF[i] for i in range(3)]
times, LX, LY, LZ, handle, bolt = [], [], [], [], [], []
for k in range(0, N + 1):
    if k <= 37: d = dl[k]
    elif k <= 44: w = path(k); d = [w[i] - OFF[i] for i in range(3)]
    elif k <= 53:
        h = HK.get(k, 1.0 if 47 <= k <= 51 else 0.0); d = [dG[0], dG[1] - PULL * h, dG[2]]
    else:
        u = 1.0 - smooth(53, N, k); d = [dG[i] * u for i in range(3)]
    times.append(round(k / FPS, 5)); LX.append(round(d[0], 4)); LY.append(round(d[1], 4)); LZ.append(round(d[2], 4))
    handle.append([round(k / FPS, 5), HK.get(k, 0.0 if k < 44 or k > 53 else 1.0)])
    bolt.append([round(k / FPS, 5), 1.0 if k <= 50 else BK.get(k, 0.0)])
def t(k): return round(k / FPS, 5)
magstate = [[0.0, 0], [t(13.4), 0], [t(14), 1], [t(21.4), 1], [t(22), 2], [t(24.4), 2], [t(25), 1], [t(36.4), 1], [t(37), 0], [t(N), 0]]
def smooth2(a, b, x): u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
hfp = [[round(k / FPS, 5), round(smooth2(37, 41, k) * (1.0 - smooth2(54, 58, k)), 4)] for k in range(0, N + 1)]    # 1인칭 보정을 끄는 가중치: 손잡이 구간 1
out = {'handlefp': hfp, 'times': times, 'LX': LX, 'LY': LY, 'LZ': LZ, 'magstate': magstate, 'boltback': bolt, 'handleback': handle, 'frames': N, 'seconds': round(N / FPS, 4), 'SC': SC, 'D_GRAB': D_GRAB, 'CORR': CORR, 'OFF': OFF, 'W_G': W_G, 'PULL': PULL, 'W_seat': W_seat,
       'events': {'grab': t(14), 'drop': t(22), 'new_mag': t(25), 'seated': t(37), 'handle_grab': t(45), 'handle_pulled': t(47), 'handle_release': t(52), 'handle_forward': t(53)},
       'max_abs': [round(max(abs(v) for v in a), 2) for a in (LX, LY, LZ)]}
json.dump(out, open(os.path.join(D, 'empty_reload_curves.json'), 'w'), indent=1)
print('EMPTY_RELOAD_CURVES_V2', N, 'frames', out['seconds'], 's  W_seat', [round(x, 1) for x in W_seat], 'W_G', W_G, 'max', out['max_abs'])
for k in (36, 37, 39, 41, 43, 45, 47, 51, 53, 56, 60): print(k, times[k], LX[k], LY[k], LZ[k], 'abs wrist', [round(v + o, 1) for v, o in zip((LX[k], LY[k], LZ[k]), OFF)])
