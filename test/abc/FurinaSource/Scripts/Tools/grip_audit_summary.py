"""Data/grip_audit_*.json -> 무기 × 손 표(최대 틈·최대 파고듦·실패 부위) Data/grip_audit_summary.json + 화면 출력"""
import json, glob, os, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'Data')
rows = {}
for f in glob.glob(os.path.join(D, 'grip_audit_*__*__*.json')):
    d = json.load(open(f)); hand = os.path.basename(f)[:-5].split('__')[2]; w = d['worst']
    gap = max([v['gap_max'] for v in w.values()] or [0]); pen = max([v['pen_max'] for v in w.values()] or [0])
    rows.setdefault(d['sk'], {})[hand] = {'gap': gap, 'pen': pen, 'fail': d['fail'], 'drift': max(v['pos_cm'] for v in d['wrist_drift_vs_gun'].values())}
json.dump(rows, open(os.path.join(D, 'grip_audit_summary.json'), 'w'), indent=1)
for sk, hs in sorted(rows.items()):
    bad = {h: v['fail'] for h, v in hs.items() if v['fail']}
    print('%-14s hands=%2d  max_gap=%.2f  max_pen=%.2f  max_drift=%.2f  fails=%s' % (sk, len(hs), max(v['gap'] for v in hs.values()), max(v['pen'] for v in hs.values()), max(v['drift'] for v in hs.values()), json.dumps(bad, ensure_ascii=False)[:600]))
