"""긴급(빈 탄창) 재장전 곡선 만들기 -> Data/empty_reload_curves.json
원본: Downloads/fps-animated-carbine/source/arms@carbine.fbx (30fps). 프레임 9~69(61프레임 = 60프레임 간격 = 2.0초)를 1:1로 쓴다(리샘플 없음).
  9~: 대기 자세 / 10~22 왼손이 탄창으로(노리쇠는 푸리나에서는 처음부터 뒤에 걸려 있음) / 23 탄창 잡음 / 23~32 탄창 뽑아 아래로 / 31 낙하 / 34 새 탄창 손에 / 36~46 삽입(46 장착)
  / 48~54 왼손이 총 위로 넘어가 노리쇠 멈치를 침 / 52~56 노리쇠 앞으로 / 58~69 손잡이로 복귀.
입력: Data/carbine_anim_f0.json(0~14), Data/carbine_anim_f1.json(14~70) (Blender sample_carbine_anim.py 출력; 총 로컬 [옆(+왼), 위, 앞] cm 환산값).
왼손 곡선(ReloadLX/LY/LZ, 푸리나 총 좌표 X왼쪽·Y앞·Z위 변위)
  변위 = (손목(f) - 손목(9)) x SC  (X=옆, Y=앞, Z=위)   SC = 0.973 (총 길이 80/74 x 푸리나 팔이 짧은 0.9 배)
  + w(f) x CORR,  CORR = D_GRAB - (손목(23) - 손목(9)) x SC : 탄창을 잡는 순간의 변위가 기존 재장전의 잡기 변위 D_GRAB(기존 곡선 reload_curves_new.json 의 잡기 구간 값)과 같아지도록 하는 보정.
  w: 9→22 부드럽게 0→1, 22~60 유지, 60→68 부드럽게 1→0 (끝에서 변위 0 = 푸리나 기본 손 위치)
MagState: 0 장착 / 1 손에 쥠 / 2 낙하(버려짐)  (기존 재장전과 같은 의미)    BoltBack: 1 = 노리쇠 완전 후퇴(걸림), 0 = 전진"""
import json, math, os
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
SC = 0.973; F0, F1 = 9, 69; FPS = 30.0
rows = {}
for fn in ('carbine_anim_f0.json', 'carbine_anim_f1.json'):
    for r in json.load(open(os.path.join(D, fn)))['samples']: rows[r['f']] = r
for f in (69, 70):
    assert f in rows, f
L = {f: rows[f]['L_wrist'] for f in range(F0, F1 + 1)}      # [옆, 위, 앞]
BZ = {f: rows[f]['bolt'][2] for f in range(F0, F1 + 1)}
old = json.load(open(os.path.join(D, 'reload_curves_new.json')))
def old_at(t, key):
    ts = old['times']; vs = old[key]
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]: return vs[i] + (vs[i + 1] - vs[i]) * (t - ts[i]) / (ts[i + 1] - ts[i])
    return vs[-1]
T_GRAB_OLD = 0.80      # 기존 재장전에서 탄창을 쥐고 대기하는 구간(0.74~0.98초)의 값
D_GRAB = [old_at(T_GRAB_OLD, 'LX'), old_at(T_GRAB_OLD, 'LY'), old_at(T_GRAB_OLD, 'LZ')]
def smooth(a, b, x): u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
def delta(f):
    l, l0 = L[f], L[F0]
    return [(l[0] - l0[0]) * SC, (l[2] - l0[2]) * SC, (l[1] - l0[1]) * SC]      # X(옆), Y(앞), Z(위)
dg = delta(23); CORR = [D_GRAB[i] - dg[i] for i in range(3)]
times, LX, LY, LZ = [], [], [], []
for f in range(F0, F1 + 1):
    w = smooth(9, 22, f) * (1.0 - smooth(60, 68, f)); d = delta(f)
    times.append(round((f - F0) / FPS, 5)); LX.append(round(d[0] + w * CORR[0], 4)); LY.append(round(d[1] + w * CORR[1], 4)); LZ.append(round(d[2] + w * CORR[2], 4))
def t(f): return round((f - F0) / FPS, 5)
magstate = [[0.0, 0], [t(22.4), 0], [t(23), 1], [t(30.4), 1], [t(31), 2], [t(33.4), 2], [t(34), 1], [t(45.4), 1], [t(46), 0], [t(F1), 0]]
bolt = []
for f in range(F0, F1 + 1):
    v = 1.0 if f <= 52 else max(0.0, min(1.0, (10.26 - BZ[f]) / 6.75)); bolt.append([t(f), round(v, 3)])
out = {'times': times, 'LX': LX, 'LY': LY, 'LZ': LZ, 'magstate': magstate, 'boltback': bolt, 'frames': F1 - F0, 'seconds': round((F1 - F0) / FPS, 4), 'SC': SC, 'D_GRAB': D_GRAB, 'CORR': CORR,
       'events': {'grab': t(23), 'drop': t(31), 'new_mag': t(34), 'seated': t(46), 'bolt_release_start': t(52), 'bolt_forward': t(56)},
       'max_abs': [round(max(abs(v) for v in a), 2) for a in (LX, LY, LZ)]}
json.dump(out, open(os.path.join(D, 'empty_reload_curves.json'), 'w'), indent=1); print('EMPTY_RELOAD_CURVES', out['frames'], 'frames', out['seconds'], 's', 'D_GRAB', [round(x, 2) for x in D_GRAB], 'max', out['max_abs'])
