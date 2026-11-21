"""사용: python side_overlay.py <태그>  -> pside_<태그>_<뷰>.png 위에 뼈 위치(빨강=오른손, 초록=왼손, 노랑=프레임 중심)를 투영한 pside_<태그>_<뷰>_ov.png 를 만든다.
카메라: 위치 cam, 중심 center 를 바라봄(롤 0), 수평 FOV 90."""
import json, sys, math
from PIL import Image, ImageDraw
T = sys.argv[1]
J = json.load(open('lyra_pistol_side_probe_%s.json' % T))
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def norm(a): l = math.sqrt(dot(a, a)); return [x / l for x in a]
for sh in J['shots']:
    n = sh['name']; base = sh.get('file', 'pside_%s_%s' % (T, n)); im = Image.open(base + '.png').convert('RGB'); W, H = im.size; dr = ImageDraw.Draw(im)
    cam = sh['cam']; fwd = norm(sub(sh['center'], cam)); up0 = [0, 0, 1]
    if abs(dot(fwd, up0)) > 0.99: up0 = [math.cos(math.radians(sh['yaw'])), math.sin(math.radians(sh['yaw'])), 0]
    rt = norm(cross(up0, fwd)); up = cross(fwd, rt); f = (W / 2) / math.tan(math.radians(45))
    def proj(P):
        d = sub(P, cam); z = dot(d, fwd)
        return (W / 2 + dot(d, rt) / z * f, H / 2 - dot(d, up) / z * f)
    for bn, P in sh['bones'].items():
        x, y = proj(P); col = (255, 0, 0) if bn.endswith('_R') or bn.startswith('Right') else (0, 255, 0)
        r = 9 if 'wrist' in bn else 6; dr.ellipse([x - r, y - r, x + r, y + r], outline=col, width=3); dr.text((x + 8, y - 8), bn.replace('Finger', 'F').replace('_R', '').replace('_L', ''), fill=col)
    x, y = proj(sh['frame_center']); dr.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(255, 255, 0), width=3)
    im.save(base + '_ov.png'); print(n, 'ok', W, H)
