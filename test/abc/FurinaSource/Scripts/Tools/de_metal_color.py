"""소총/조준경 텍스처에서 금속 부위(metallic>0.5) 평균 색(선형)·거칠기 측정 -> Data/de_metal_color.json
 사용: python de_metal_color.py"""
import json, numpy as np
from PIL import Image
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; TM = json.load(open(D + r'\de_weapons_texmap.json', encoding='utf-8'))
def lin(c): c = c / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def g(p, mode, size=512): return np.asarray(Image.open(p).convert(mode).resize((size, size)), dtype=np.float64)
R = {}
for key in ('kar98k', 'g43', 'zf4', 'mp40', 'stg44'):
    for mn, sp in TM.get(key, {}).items():
        if not sp.get('basecolor'): continue
        bc = lin(g(sp['basecolor'], 'RGB')); mt = g(sp['metallic'], 'L') / 255 if sp.get('metallic') else np.ones(bc.shape[:2])
        rg = g(sp['roughness'], 'L') / 255 if sp.get('roughness') else None
        m = mt > 0.5; frac = float(m.mean())
        if frac < 0.02: R['%s/%s' % (key, mn)] = {'metal_frac': round(frac, 3)}; continue
        R['%s/%s' % (key, mn)] = {'metal_frac': round(frac, 3), 'lin_rgb': bc[m].mean(0).round(4).tolist(), 'median': np.median(bc[m], 0).round(4).tolist(), 'rough': round(float(rg[m].mean()), 3) if rg is not None else None}
json.dump(R, open(D + r'\de_metal_color.json', 'w'), indent=1); print(json.dumps(R, indent=0))
