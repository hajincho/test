"""python img_sheet.py <출력.jpg> <열 수> <폭> <이미지1> [이미지2 ...]   : 캡처 여러 장을 이름표를 붙여 한 장으로 (jpg)"""
import sys, os
from PIL import Image, ImageDraw
out, cols, wd = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); files = [f for f in sys.argv[4:] if os.path.exists(f)]
ims = []
for f in files:
    im = Image.open(f).convert('RGB'); h = int(im.size[1] * wd / im.size[0]); im = im.resize((wd, h)); d = ImageDraw.Draw(im)
    lab = os.path.splitext(os.path.basename(f))[0]; d.rectangle([0, 0, 8 * len(lab) + 8, 18], fill=(0, 0, 0)); d.text((4, 3), lab, fill=(255, 255, 0)); ims.append(im)
rows = (len(ims) + cols - 1) // cols; hh = max(i.size[1] for i in ims)
sheet = Image.new('RGB', (cols * wd, rows * hh), (30, 30, 30))
for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * wd, (k // cols) * hh))
sheet.save(out, quality=88); print('sheet', out, sheet.size, len(ims))
