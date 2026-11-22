"""blender -b --python fpvm_place_search.py -- <json 입력>  (2026-11-22)
긴 총(MG34 등)의 1인칭 배치 찾기: 두 손이 어깨에서 닿으면서(오른손 = 손잡이, 왼손 = 받침점) 화면(가로 FOV 85°, 16:9)에 보여야 할 점들
(드럼·리시버·왼손 받침)이 시야 안 아래쪽 오른편에 들어오는 총 위치·회전을 격자 탐색.
입력 json: {"grip": [x,y,z], "holds": [[x,y,z], ...](후보), "show": [[x,y,z], ...], "butt_y": 61, "reach": 37.5}
출력: 가장 좋은 gun_pos(cm), gun_rot(°), hold 와 점수. 좌표는 정리본 원래 좌표(cm, 총구 -Y)."""
import sys, json, math, itertools
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
from mathutils import Vector
import fpvm_lib as L
A = json.loads(sys.argv[sys.argv.index('--') + 1])
SH = {'L': Vector((-10.73, 9.89, -16.11)) / 100, 'R': Vector((-17.46, -9.78, -17.09)) / 100}
REACH = A.get('reach', 37.5) / 100; HF = math.radians(85 / 2); VF = math.atan(math.tan(HF) * 9 / 16)


def ang(p):
    return math.atan2(-p.y, p.x), math.atan2(p.z, p.x)


best = None
for gx in range(A.get('gx_min', -10), 46, 2):
    for gy in (-2, -4, -6, -9, -12):
        for gz in (-6, -8, -10, -12, -14):
            for rz in (-4.0, -2.0, 2.0, 6.0):
                for ry in (-4.0, 0.0, 4.0):
                    G = L.gun_native_to_cam([gx, gy, gz], 2.5, rz, ry)
                    g = G @ Vector(A['grip'])
                    if (g - SH['R']).length > REACH + 0.015: continue
                    for h in A['holds']:
                        hw = G @ Vector(h)
                        if (hw - SH['L']).length > REACH + A.get('l_slack', 0.01): continue
                        pts = [hw] + [G @ Vector(p) for p in A['show']]
                        sc = 0.0
                        for p in pts:
                            if p.x < 0.05: sc += 10; continue
                            sc += max(0, A.get('min_dist', 0) / 100 - p.length) * 30
                            a, b = ang(p)
                            sc += max(0, abs(a) - HF * 0.9) * 20 + max(0, -b - VF * 0.85) * 20 + max(0, b + 0.05) * 5
                        mz = G @ Vector((A['grip'][0], -60, A.get('bore_z', 3)))   # 총구가 화면 가운데 근처로
                        a, b = ang(mz); sc += 0.5 * abs(a - math.radians(-8)) + 0.5 * abs(b - math.radians(-6))
                        if best is None or sc < best[0]: best = (sc, [gx, gy, gz], [2.5, rz, ry], h, [round(math.degrees(v), 1) for p in pts for v in ang(p)])
print('PLACE', json.dumps({'score': round(best[0], 3), 'gun_pos': best[1], 'gun_rot': best[2], 'hold': best[3], 'angles': best[4]}))
