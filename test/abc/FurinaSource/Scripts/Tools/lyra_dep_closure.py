"""Lyra L_FiringRange_WP 의존 에셋 폐포 계산 (uasset 이름 테이블의 패키지 경로 문자열을 스캔).
사용: python lyra_dep_closure.py [최대깊이] -> Data/lyra_closure.json (files, depth, sizes)"""
import re, os, json, sys
L = r'C:\Users\fromj\Downloads\test\test\abc'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_closure.json'
MOUNT = {'Game': os.path.join(L, 'Content')}
for dp in (os.path.join(L, 'Plugins'), os.path.join(L, 'Plugins', 'GameFeatures')):
    for p in os.listdir(dp):
        c = os.path.join(dp, p, 'Content')
        if os.path.isdir(c): MOUNT.setdefault(p, c)
rx = re.compile(rb'/(' + '|'.join(re.escape(k) for k in MOUNT).encode() + rb')/[A-Za-z0-9_/\-\.]+')
def path_of(pkg):
    parts = pkg.split('/')
    base = os.path.join(MOUNT[parts[1]], *parts[2:])
    for ext in ('.uasset', '.umap'):
        if os.path.isfile(base + ext): return base + ext
    return None
SM = MOUNT['ShooterMaps']
seeds = [os.path.join(SM, 'Maps', 'L_FiringRange_WP.umap')]
for d in (os.path.join(SM, '__ExternalActors__', 'Maps', 'L_FiringRange_WP'), os.path.join(SM, '__ExternalObjects__', 'Maps', 'L_FiringRange_WP'), os.path.join(SM, 'Maps', 'DataLayers')):
    for dp, _, fs in os.walk(d):
        seeds += [os.path.join(dp, f) for f in fs]
MAXD = int(sys.argv[1]) if len(sys.argv) > 1 else 99
seen, order, depth, missing = set(), [], {}, set()
stack = [(s, 0) for s in seeds]
while stack:
    f, d = stack.pop()
    if f in seen: continue
    seen.add(f); order.append(f); depth[f] = d
    if d >= MAXD: continue
    try: data = open(f, 'rb').read()
    except Exception: continue
    for m in rx.finditer(data):
        pkg = m.group(0).decode().split('.')[0]
        if pkg.endswith('/'): continue
        p = path_of(pkg)
        if p: stack.append((p, d + 1))
        else: missing.add(pkg)
sizes = {}
for f in order:
    k = 'external' if '__External' in f else max((m for m, c in MOUNT.items() if f.startswith(c)), key=lambda m: len(MOUNT[m]))
    sizes.setdefault(k, [0, 0]); sizes[k][0] += 1; sizes[k][1] += os.path.getsize(f)
print(MAXD, {k: (v[0], round(v[1] / 1e6, 1)) for k, v in sizes.items()}, 'total MB', round(sum(v[1] for v in sizes.values()) / 1e6, 1))
json.dump({'files': order, 'depth': depth, 'sizes': sizes, 'missing_sample': sorted(missing)[:40]}, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
