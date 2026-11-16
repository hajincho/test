"""Builds the asset packages for the laptop (2026-11-16) in C:\\Users\\fromj\\OneDrive\\바탕 화면\\새 폴더\\furina_assets_for_laptop (a new folder; nothing else in OneDrive is touched):
  1_furina_core.zip          Content/Furina (everything), the changed ThirdPersonCharacter_BP + ExampleLevel, FurinaSource (README, Scripts, Data, FBX, Textures; without Backups / renders / _prev)
  2_niagara_examples.zip     Content/NiagaraExamples (Niagara Examples pack incl. the NS_MuzzleFlash used for the muzzle fire)
  3_colt_original_model.zip  Downloads/colt-m4a1-carbine (source FBX + original 4096 textures)
Paths inside the zips of 1 and 2 are relative to the UE project root (the folder with abc.uproject): extract them there. Zip 3 has the top folder colt-m4a1-carbine/.
The Underground Tunnel map content is NOT included (the user will find the map later)."""
import os, zipfile, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\fromj\Downloads\test\test\abc'; OUT = r'C:\Users\fromj\OneDrive\바탕 화면\새 폴더\furina_assets_for_laptop'
os.makedirs(OUT, exist_ok=True)
def walk(d):
    for r, _, fs in os.walk(d):
        for f in fs: yield os.path.join(r, f)
def add(zf, files, base, prefix=''):
    n = 0; tot = 0
    for f in files:
        rel = os.path.relpath(f, base).replace('\\', '/'); zf.write(f, prefix + rel); n += 1; tot += os.path.getsize(f)
    return n, tot
t0 = time.time(); stats = {}
# 1 core
files = list(walk(os.path.join(ROOT, 'Content', 'Furina')))
files += [os.path.join(ROOT, 'Content', '3DPlatformerGameBundle', 'Demo', 'ThirdPersonAssets', 'Blueprints', 'ThirdPersonCharacter_BP.uasset'), os.path.join(ROOT, 'Content', '3DPlatformerGameBundle', 'Levels', 'ExampleLevel.umap')]
for f in walk(os.path.join(ROOT, 'FurinaSource')):
    rel = os.path.relpath(f, os.path.join(ROOT, 'FurinaSource')).replace('\\', '/')
    if rel.startswith('Backups/') or rel.startswith('Data/renders/') or '_prev' in rel or '_old_ar15' in rel: continue
    files.append(f)
with zipfile.ZipFile(os.path.join(OUT, '1_furina_core.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z: stats['1_furina_core.zip'] = add(z, files, ROOT)
print('1 done', stats['1_furina_core.zip'], round(time.time() - t0), 's', flush=True)
with zipfile.ZipFile(os.path.join(OUT, '2_niagara_examples.zip'), 'w', zipfile.ZIP_STORED) as z: stats['2_niagara_examples.zip'] = add(z, list(walk(os.path.join(ROOT, 'Content', 'NiagaraExamples'))), ROOT)
print('2 done', stats['2_niagara_examples.zip'], round(time.time() - t0), 's', flush=True)
COLT = r'C:\Users\fromj\Downloads\colt-m4a1-carbine'
with zipfile.ZipFile(os.path.join(OUT, '3_colt_original_model.zip'), 'w', zipfile.ZIP_STORED) as z: stats['3_colt_original_model.zip'] = add(z, list(walk(COLT)), os.path.dirname(COLT))
print('3 done', stats['3_colt_original_model.zip'], round(time.time() - t0), 's', flush=True)
lines = ['Furina 프로젝트 에셋 묶음 (집 컴퓨터에서 만든 최신 상태, 2026-11-16)', '', '프로젝트 루트 = abc.uproject가 있는 폴더. 1번과 2번 zip은 그 폴더에 풀어서 덮어쓰기 하세요. 3번은 아무 곳에나 풀어도 됩니다(경로는 스크립트가 colt-m4a1-carbine 폴더를 가정).', '']
for k, (n, tot) in stats.items(): lines.append('%s : 파일 %d개, 원본 합계 %.0f MB' % (k, n, tot / 1048576))
lines += ['', '언더그라운드 터널 맵 콘텐츠는 포함하지 않았습니다.', '에디터를 닫은 상태에서 덮어쓰고, 처음 열 때 셰이더·텍스처 빌드로 오래 걸릴 수 있습니다.']
open(os.path.join(OUT, 'MANIFEST.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('ALL DONE', round(time.time() - t0), 's', flush=True)
