"""Summarises ue_playtest.json per phase (idle / walk / sprint)."""
import json, math, sys
D = sys.argv[1]
rows = [r for r in json.load(open(D + r'\ue_playtest.json')) if 'err' not in r]
errs = [r for r in json.load(open(D + r'\ue_playtest.json')) if 'err' in r]
print('rows', len(rows), 'errors', len(errs), errs[:1])
REF = {'h_F_17_1_L': [9.0, 48.1, -42.8], 'h_F_17_1_R': [-9.0, 48.1, -42.8], 'h_F_8_1_L': [9.7, 24.8, -21.1],
       'h_CF_2_L': [7.4, 1.4, 3.2], 'h_CF_2_R': [-7.4, 1.4, 3.2], 'h_DM_5_1': [-10.2, -31.8, 9.1], 'h_DM_3_1': [-12.2, -25.9, 12.9]}
def phase(r): return 'idle' if r['v'] < 5 else ('walk' if r['v'] < 200 else 'sprint')
groups = {}
for r in rows: groups.setdefault(phase(r), []).append(r)
for k, g in groups.items():
    avg = lambda key: round(sum(r[key] for r in g) / len(g), 3)
    print('\n==', k, 'n', len(g), 'v', avg('v'), 'maxWalk', sorted(set(r['mws'] for r in g)))
    print('  curves', {c: (round(min(r[c] for r in g), 2), round(max(r[c] for r in g), 2)) for c in ('FurinaIdle', 'FurinaWalk', 'HairDyn', 'IdleBlink', 'DbgL', 'DbgR', 'DbgW', 'DbgC')})
    sp = [abs(r['Left-ankle'][0] - r['Right-ankle'][0]) for r in g]
    print('  feet X spread mean %.1f max %.1f' % (sum(sp) / len(sp), max(sp)), ' knee X spread mean %.1f' % (sum(abs(r['Left-knee'][0] - r['Right-knee'][0]) for r in g) / len(g)))
    st = [abs(r['Left-ankle'][1] - r['Right-ankle'][1]) for r in g]
    print('  stride (fore-aft) max %.1f mean %.1f   max ankle Z %.1f' % (max(st), sum(st) / len(st), max(max(r['Left-ankle'][2], r['Right-ankle'][2]) for r in g)))
    print('  ankle Z L/R mean %.1f %.1f  toe Z %.1f %.1f  hipsZ %.1f' % tuple(sum(r[b][2] for r in g) / len(g) for b in ('Left-ankle', 'Right-ankle', 'Left-toe', 'Right-toe', 'Hips')))
    for h, ref in REF.items():
        offs = [math.dist(r[h], ref) for r in g]
        mean = [sum(r[h][i] for r in g) / len(g) for i in range(3)]
        jit = max(math.dist(r[h], mean) for r in g)
        print('  %-12s off mean %5.1f max %5.1f  spread %5.1f  mean %s' % (h, sum(offs) / len(offs), max(offs), jit, [round(x, 1) for x in mean]))
