"""M4 팩 Reload(Data/m4_reload_extract.json)로 푸리나 재장전 곡선을 만든다 -> Data/reload_curves_new.json
구성 (총 3.0초, 30fps 샘플):
  0.00-0.05  대기
  S1  팩 f7 -> f26   왼손이 핸드가드에서 탄창으로 (잡기까지)
  S2  팩 f26 -> f36  탄창을 잡고 아래로 뽑는다 (f27 쯤 MagState 1 = 손에 쥠, f36 에 놓음 = 2)
  GAP 0.70s          허리춤으로 가서 새 탄창을 꺼내 올려 팩 f43 자세에 도착 (0.25 이동 + 0.20 꺼내기 + 0.25 올리기)
  S4  팩 f43 -> f64  새 탄창을 총으로 가져가 꽂는다 (f62 쯤 MagState 0 = 장착)
  S5  팩 f64 -> f82  왼손이 핸드가드로 복귀
팩 속도는 S1+S2+S4+S5 = 68프레임(2.267s)을 2.25s 에 맞춘다(0.99배). 푸리나 팔이 짧아 이동량은 0.9배(기존과 동일).
왼손 델타 = (손 위치 - 프레임1 손 위치) 를 총 기준 (X왼쪽, Y앞, Z위) cm 로.  허리춤 점은 기존 템플릿 재장전의 새 탄창 자세 (16.4, -36.9, -32.8)."""
import json, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
fr = json.load(open(D + r'\m4_reload_extract.json', encoding='utf-8'))['frames']
K = 0.9
base = fr['1']['LeftHand']
def P(f):     # 팩 프레임 f(실수 가능) 의 왼손 델타 (선형 보간)
    f0 = max(1, min(110, int(math.floor(f)))); f1 = min(110, f0 + 1); a = f - f0
    a0, a1 = fr[str(f0)]['LeftHand'], fr[str(f1)]['LeftHand']
    return [((a0[i] * (1 - a) + a1[i] * a) - base[i]) * K for i in range(3)]
def lerp(a, b, u): return [a[i] * (1 - u) + b[i] * u for i in range(3)]
def smooth(u): return u * u * (3 - 2 * u)
BELT = [16.4, -36.9, -32.8]
s = 2.25 / (68 / 30.0)          # 팩 시간 배율
T0 = 0.05
segs = []   # (t_start, t_end, fn(u)->delta)
t = T0
def add_pack(f_a, f_b):
    global t
    dur = (f_b - f_a) / 30.0 * s
    segs.append((t, t + dur, (lambda fa, fb: (lambda u: P(fa + (fb - fa) * u)))(f_a, f_b))); t += dur
add_pack(7, 26); t_grip_end = t
add_pack(26, 36); t_release = t
Rpose = P(36); Epose = P(43)
t_gap0 = t
segs.append((t, t + 0.25, lambda u: lerp(Rpose, BELT, smooth(u)))); t += 0.25
t_belt = t
segs.append((t, t + 0.20, lambda u: [BELT[0], BELT[1], BELT[2] - 2.0 * math.sin(math.pi * u)])); t += 0.20   # 꺼낼 때 살짝 아래로
t_fresh = t - 0.10
segs.append((t, t + 0.25, lambda u: lerp(BELT, Epose, smooth(u)))); t += 0.25
t_gap1 = t
add_pack(43, 64); t_seat = t
add_pack(64, 82); t_end = t
def delta_at(tt):
    if tt <= T0: return [0.0, 0.0, 0.0]
    if tt >= t_end: return [0.0, 0.0, 0.0]
    for a, b, fn in segs:
        if a <= tt <= b: return fn((tt - a) / (b - a))
    return [0.0, 0.0, 0.0]
n = int(round(3.1333 * 30)) + 1
times = [round(i / 30.0, 5) for i in range(n)]
cols = [[round(delta_at(tt)[c], 3) for tt in times] for c in range(3)]
# MagState 키: 0 장착 / 1 손에 쥠 / 2 없음(버려짐, 아직 새것 없음). (전환 폭 0.06s)
t_grab = T0 + (26 - 7) / 30.0 * s + (27 - 26) / 30.0 * s      # 팩 f27: 탄창이 움직이기 직전에 쥠으로 전환
t_in = t_gap1 + (62 - 43) / 30.0 * s                          # 팩 f62: 거의 끼워진 시점
mag = [(0.0, 0), (t_grab - 0.03, 0), (t_grab + 0.03, 1), (t_release - 0.03, 1), (t_release + 0.03, 2),
       (t_fresh - 0.03, 2), (t_fresh + 0.03, 1), (t_in - 0.03, 1), (t_in + 0.03, 0), (3.1333, 0)]
ev = dict(grab=t_grab, release=t_release, belt_arrive=t_belt, fresh_in_hand=t_fresh, gap_end=t_gap1, seated=t_in, home=t_end)
json.dump({'times': times, 'LX': cols[0], 'LY': cols[1], 'LZ': cols[2], 'magstate': [[round(a, 4), b] for a, b in mag], 'events': {k: round(v, 3) for k, v in ev.items()},
           'max_abs': [round(max(abs(v) for v in c), 1) for c in cols], 'pack_scale_s': s}, open(D + r'\reload_curves_new.json', 'w'), indent=1)
print({k: round(v, 3) for k, v in ev.items()}, 'max', [round(max(abs(v) for v in c), 1) for c in cols], 'samples', n)
