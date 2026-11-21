"""python de_weapons_texmap.py : Data/de_weapons_build.json 의 머티리얼 이름/노드 텍스처 + 텍스처 폴더 파일명으로 머티리얼별 PBR 맵 결정 -> Data/de_weapons_texmap.json
 결과: {무기: {머티리얼: {basecolor, normal, roughness, metallic, ao, normal_gl(bool), plain(색, 텍스처 없을 때)}}}"""
import json, os, re, glob
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; SRC = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany'
B = json.load(open(D + r'\de_weapons_build.json', encoding='utf-8'))
TEXDIR = {'p38': 'p38/textures', 'p08': 'p08/textures', 'pp': 'pp/textures', 'kar98k': 'kar98k/textures', 'g43': 'g43/textures', 'stg44': 'stg44/textures', 'mp40': 'mp40/textures',
          'mp38': 'mp38/textures', 'mg42': 'mg42/textures', 'mg34': 'mg34/textures', 'panzerfaust': 'panzerfaust/textures', 'panzerschreck': 'panzerschreck/textures',
          'panzerschreck_rocket': 'panzerschreck/Panzerschreck_Rocket/textures', 'pzb39': 'PzB39/textures', 'grw34': 'grw34/textures', 'zf4': 'zf4_scope/textures', 'ammo_7_92x94': '7_92x94_ammo/textures'}
PLAIN = {'mortar_shell': (0.18, 0.2, 0.15, 0.4, 0.55), 'zf39': (0.04, 0.04, 0.045, 0.9, 0.35), 'zf41': (0.04, 0.04, 0.045, 0.9, 0.35), 'mauser_clip': (0.62, 0.45, 0.2, 1.0, 0.3)}   # 색 RGB, 금속, 거칠기
KIND = [('basecolor', r'(basecolor|base_color|albedo|_d$|_a2?$|color_\d+$)'), ('normal', r'(normal|_n$|_n_n$)'), ('roughness', r'(roughness|_r\d*$)'), ('metallic', r'(metallic)'), ('ao', r'(_ao$|mixed_ao)')]
def norm(s): return re.sub(r'[^0-9a-zа-яё]', '', s.lower())
def stem(f):
    b = os.path.basename(f).lower()
    for ext in ('.tga.png', '.png', '.jpeg', '.jpg', '.tga'):
        if b.endswith(ext): return b[:-len(ext)]
    return b
def kind_of(st):
    for k, rx in KIND:
        if re.search(rx, st): return k
    return None
def base_of(st):
    return re.sub(r'(_?(basecolor|base_color|albedo|normal_directx|normal_gl|normalgl|normal|roughness|metallic|mixed_ao|ao|height|emissive|opacity|d|a2?|n_n|n_s|n|r\d*))$', '', st)
OUT = {}
for key, e in B.items():
    if 'materials' not in e: continue
    mats = list(e.get('mat_faces', {}).keys()) or list(e['materials'].keys())
    files = sorted(glob.glob(os.path.join(SRC, TEXDIR[key], '*'))) if key in TEXDIR else []
    res = {}
    for m in mats:
        r = {}
        if key in PLAIN: r['plain'] = PLAIN[key]
        cand = list(e['materials'].get(m, {}).get('node_textures', []))
        if not cand:
            nm = norm(m)
            cand = [f for f in files if norm(base_of(stem(f))) == nm or norm(base_of(stem(f))).endswith(nm) and len(nm) >= 3]
        if key == 'pp':
            big = max(e['mat_faces'], key=e['mat_faces'].get); pre = 'walther_pp_main_tex' if m == big else 'walther_pp_ammo_tex'
            cand = [f for f in files if stem(f).startswith(pre)]
        if key == 'grw34': cand = files; r['basecolor'] = files[0] if files else None
        if key in ('g43',): cand = [f for f in files if stem(f).startswith('gewehr43')]
        for f in cand:
            k = kind_of(stem(f))
            if k and k not in r: r[k] = f
        if 'normal' in r: r['normal_gl'] = 'directx' not in stem(r['normal'])
        res[m] = r
    OUT[key] = res
json.dump(OUT, open(D + r'\de_weapons_texmap.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for k, v in OUT.items():
    for m, r in v.items(): print(k, '|', m, '|', {kk: (os.path.basename(vv) if isinstance(vv, str) else vv) for kk, vv in r.items()})
