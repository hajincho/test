"""푸리나(캐릭터/총기/화염/모션/HUD/입력) 내보내기 매니페스트 생성.
시드: 푸리나 폰 BP + Content/Furina 전체(Lyra 전용 Furina/Lyra 제외) -> /Game 의존 폐포 계산(uasset 이름 테이블의 패키지 경로 스캔).
폐포에 들어온 파일 중 푸리나 관련 루트(Furina, 3DPlatformerGameBundle, TFPMovement, Free_Crawl_Animation, NiagaraExamples)는 내보내기 대상,
그 밖의 루트(Lyra 자체 에셋 등)는 'external_deps'로 따로 기록(내보내지 않음).
출력: FurinaSource/Export/furina_export_manifest.json
  files: [{path(Content 기준, 확장자 포함), size, category, group}]   categories/groups/total 요약 포함"""
import re, os, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))      # 프로젝트 루트
C = os.path.join(ROOT, 'Content')
OUT = os.path.join(ROOT, 'FurinaSource', 'Export', 'furina_export_manifest.json')
PAWN = 'Furina/../3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OWN = ('Furina', '3DPlatformerGameBundle', 'TFPMovement', 'Free_Crawl_Animation', 'NiagaraExamples')
rx = re.compile(rb'/Game/[A-Za-z0-9_/\-\.]+')
def path_of(pkg):
    base = os.path.join(C, *pkg.split('/')[2:])
    for ext in ('.uasset', '.umap'):
        if os.path.isfile(base + ext): return base + ext
    return None
seeds = []
for dp, _, fs in os.walk(os.path.join(C, 'Furina')):
    if os.path.normpath(dp).startswith(os.path.join(C, 'Furina', 'Lyra')): continue
    seeds += [os.path.join(dp, f) for f in fs if f.endswith(('.uasset', '.umap'))]
seeds.append(os.path.join(C, '3DPlatformerGameBundle', 'Demo', 'ThirdPersonAssets', 'Blueprints', 'ThirdPersonCharacter_BP.uasset'))
seen, order, ext_deps, stack = set(), [], {}, list(seeds)
while stack:
    f = stack.pop()
    if f in seen: continue
    seen.add(f)
    rel = os.path.relpath(f, C).replace(os.sep, '/')
    if rel.split('/')[0] not in OWN:                     # Lyra 등 외부 에셋: 기록만 하고 더 따라가지 않는다
        ext_deps[rel] = ext_deps.get(rel, 0) + 1; continue
    order.append(f)
    try: data = open(f, 'rb').read()
    except Exception: continue
    for m in rx.finditer(data):
        pkg = m.group(0).decode().split('.')[0]
        if pkg.endswith('/'): continue
        p = path_of(pkg)
        if p: stack.append(p)
def classify(rel):
    p = rel.lower()
    if rel.startswith('Furina/M4/'):
        if '/t_colt_' in p or 'm_colt' in p or p.endswith(('m_brass.uasset', 'm_copper.uasset', 'm_m4_ar1.uasset', 'm_m4_ar2.uasset', 'm_m4_ar3.uasset', 'm_m4_ar4.uasset')): return ('Weapon', 'M4A1 소총 모델/재질/텍스처')
        if 'flash' in p or 'muzzle' in p: return ('FX', '총구 화염')
        if '223case' in p or 'magdrop' in p or 'ricospark' in p or 'bulletglow' in p or 'projectile' in p: return ('FX', '탄피/버린 탄창/도탄 스파크/총알 모양')
        return ('Weapon', 'M4A1 소총 모델/재질/텍스처')
    if rel.startswith('Furina/FP/'): return ('Weapon', '1인칭 소총/총알/HUD 기반') if 'Weapon' in rel or 'Bullet' in rel else ('Animation', '1인칭 모션(재장전/사격/Manny 템플릿)')
    if rel.startswith('Furina/TFP/') or rel.startswith('Furina/Crawl/') or rel.startswith('Furina/Anim/') or rel.startswith('Furina/Retarget/'): return ('Animation', '3인칭/포복/리타깃 모션')
    if rel.startswith('Furina/Input/'): return ('Input', '입력 액션/매핑')
    if rel.startswith('Furina/UI/'): return ('HUD', '탄약 HUD')
    if rel.startswith('Furina/Textures/') or rel.startswith('Furina/Materials/') or rel.startswith('Furina/SK_Furina') or rel.startswith('Furina/CR_') or rel.startswith('Furina/ABP_'): return ('Character', '푸리나 메시/재질/스켈레톤/애님BP/컨트롤 릭')
    if rel.startswith('Furina/QA/'): return ('QA', '검증용')
    if rel.startswith('3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'): return ('Character', '푸리나 폰 블루프린트(모든 기능 포함)')
    if rel.startswith('3DPlatformerGameBundle/'): return ('Dependency', '플랫포머 번들 의존(컴포넌트/모션/나이아가라/오디오/위젯)')
    if rel.startswith('TFPMovement/'): return ('Dependency', 'TFP 이동 모션 의존')
    if rel.startswith('Free_Crawl_Animation/'): return ('Dependency', '포복 모션 의존')
    if rel.startswith('NiagaraExamples/'): return ('Dependency', '나이아가라 예제 FX(총구 화염 등) 의존')
    return ('Other', '')
files = []
for f in sorted(order):
    rel = os.path.relpath(f, C).replace(os.sep, '/'); cat, grp = classify(rel)
    files.append({'path': rel, 'size': os.path.getsize(f), 'category': cat, 'group': grp})
summ = {}
for x in files:
    s = summ.setdefault(x['category'], {'files': 0, 'bytes': 0}); s['files'] += 1; s['bytes'] += x['size']
lyra_only = [os.path.relpath(os.path.join(dp, f), C).replace(os.sep, '/') for dp, _, fs in os.walk(os.path.join(C, 'Furina', 'Lyra')) for f in fs if f.endswith('.uasset')]
lyra_only.append('System/Experiences/B_Furina_Experience.uasset')
res = {'engine': '5.8', 'files': files, 'summary': summ, 'total_files': len(files), 'total_bytes': sum(x['size'] for x in files),
       'external_deps_not_exported': sorted(ext_deps), 'lyra_only_assets': lyra_only}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('exported files', len(files), 'MB', round(res['total_bytes'] / 1e6, 1)); print({k: (v['files'], round(v['bytes'] / 1e6, 1)) for k, v in summ.items()}); print('external deps:', res['external_deps_not_exported'][:20])
