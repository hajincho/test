"""python sheet6.py <prefix> <out.jpg> : Data/<prefix>_{left,right,top,bottom,front,back}.png 6장을 3x2 한 장으로"""
import sys
from PIL import Image, ImageDraw
pre, out = sys.argv[1], sys.argv[2]; V = ['left', 'right', 'top', 'bottom', 'front', 'back']
W = Image.new('RGB', (1200, 800), 'white'); d = ImageDraw.Draw(W)
for i, v in enumerate(V):
    W.paste(Image.open(f'{pre}_{v}.png').convert('RGB').resize((400, 400)), ((i % 3) * 400, (i // 3) * 400)); d.text(((i % 3) * 400 + 6, (i // 3) * 400 + 6), v, fill='red')
W.save(out, quality=88)
