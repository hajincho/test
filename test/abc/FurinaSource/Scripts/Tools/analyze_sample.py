import json, sys, math
S = sys.argv[1]
rows = [r for r in json.load(open(S + r'\ue_sample.json')) if 'err' not in r]
errs = [r for r in json.load(open(S + r'\ue_sample.json')) if 'err' in r]
print('frames', len(rows), 'errors', len(errs), errs[:1])
bones = [k for k in rows[0] if k not in ('t', 'v', 'idle')]
rest = rows[0]
# speed / idle timeline (every ~0.5 s)
last = -1
for r in rows:
    if r['t'] - last >= .5:
        last = r['t']
        off = {b: round(math.dist(r[b], rest[b]), 1) for b in ('HB2_18_1', 'HB1_7_4', 'F_17_1_L', 'DM_5_1')}
        print('t=%.1f v=%6.1f idle=%.2f' % (r['t'], r['v'], r['idle']), off)
# jitter: frame-to-frame second difference of tip positions (cm)
for b in bones:
    worst = 0
    for a, m, c in zip(rows, rows[1:], rows[2:]):
        acc = math.dist([2 * y - x - z for x, y, z in zip(a[b], m[b], c[b])], [0, 0, 0])
        worst = max(worst, acc)
    maxdev = max(math.dist(r[b], rest[b]) for r in rows)
    print('%-10s maxdev %.1f cm  max jerk %.2f cm' % (b, maxdev, worst))
