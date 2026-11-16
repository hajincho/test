"""abc 프로젝트에서 푸리나 폰/콘텐츠가 의존하는 /Game 에셋 폐포 -> Data/abc_closure.json (files: abc/Content 상대경로)
시드: Furina/ 전체 + ThirdPersonCharacter_BP + 3DPlatformerGameBundle/Demo/ThirdPersonAssets (입력/위젯 포함)"""
import re, os, json
C = r'C:\Users\fromj\Downloads\test\test\abc\Content'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\abc_closure.json'
rx = re.compile(rb'/Game/[A-Za-z0-9_/\-\.]+')
def path_of(pkg):
    base = os.path.join(C, *pkg.split('/')[2:])
    for ext in ('.uasset', '.umap'):
        if os.path.isfile(base + ext): return base + ext
    return None
seeds = []
for sub in ('Furina', os.path.join('3DPlatformerGameBundle', 'Demo', 'ThirdPersonAssets')):
    for dp, _, fs in os.walk(os.path.join(C, sub)):
        seeds += [os.path.join(dp, f) for f in fs if f.endswith(('.uasset', '.umap'))]
seen, order, stack, missing = set(), [], list(seeds), set()
while stack:
    f = stack.pop()
    if f in seen: continue
    seen.add(f); order.append(f)
    try: data = open(f, 'rb').read()
    except Exception: continue
    for m in rx.finditer(data):
        pkg = m.group(0).decode().split('.')[0]
        if pkg.endswith('/'): continue
        p = path_of(pkg)
        if p: stack.append(p)
        else: missing.add(pkg)
top = {}
for f in order:
    rel = os.path.relpath(f, C).replace(os.sep, '/'); k = '/'.join(rel.split('/')[:2]); top.setdefault(k, [0, 0]); top[k][0] += 1; top[k][1] += os.path.getsize(f)
tot = sum(v[1] for v in top.values())
print('files', len(order), 'MB', round(tot / 1e6, 1))
for k, v in sorted(top.items(), key=lambda kv: -kv[1][1])[:25]: print(round(v[1] / 1e6, 1), v[0], k)
json.dump({'files': [os.path.relpath(f, C).replace(os.sep, '/') for f in order], 'missing': sorted(missing)[:60]}, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
