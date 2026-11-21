"""blender -b --python fpvm_muzzle_points.py : 소총·기관단총 1인칭 총구 위치(2026-11-21). 무기 원본에서 가장 앞 조각의 가운데(총구 둘레 중심)를 구해
 각 뷰모델의 정지 자세(GUN_POS/GUN_ROT) 로 UE 카메라 공간 cm·총열 방향으로 바꿈 -> Data/fpvm_muzzle.json (권총은 fpvm_pistols2.py 가 fpvm_<key>_stances.json 에)"""
import bpy, json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
import fpvm_lib as L
D = L.D; OUT = {}
POSE = {'kar98k': ([32.0, -9.0, -12.5], [2.5, 4.0, -3.0]), 'g43': ([29.0, -9.0, -11.2], [2.5, 4.0, -3.0])}
for k in ('mp40', 'mp38', 'stg44'):
    d = json.load(open(os.path.join(D, 'Data', 'fpvm_%s_ads_in.json' % k))); POSE[k] = (d['gun_pos'], d['gun_rot'])
for k, (pos, rot) in POSE.items():
    g = L.load_weapon(k); P = np.array([v.co[:] for v in g.data.vertices]); ymin = P[:, 1].min()
    info = {}
    for w in (0.3, 1.0, 2.0):
        s = P[P[:, 1] < ymin + w]; info['slice%.1f' % w] = {'n': len(s), 'x': [round(float(s[:, 0].min()), 2), round(float(np.median(s[:, 0])), 2), round(float(s[:, 0].max()), 2)],
                                                            'z': [round(float(s[:, 2].min()), 2), round(float(np.median(s[:, 2])), 2), round(float(s[:, 2].max()), 2)]}
    s = P[P[:, 1] < ymin + 0.3]; mz = Vector((float((s[:, 0].min() + s[:, 0].max()) / 2), float(ymin), float((s[:, 2].min() + s[:, 2].max()) / 2)))
    G0 = L.gun_native_to_cam(pos, *rot); wm = G0 @ mz; fw = (G0.to_3x3() @ Vector((0, -1, 0))).normalized(); up = (G0.to_3x3() @ Vector((0, 0, 1))).normalized()
    OUT[k] = {'native_cm': [round(c, 3) for c in mz], 'ue_cam_cm': [wm.x * 100, -wm.y * 100, wm.z * 100], 'ue_fwd': [fw.x, -fw.y, fw.z], 'ue_up': [up.x, -up.y, up.z], 'slices': info}
    bpy.data.objects.remove(g)
json.dump(OUT, open(os.path.join(D, 'Data', 'fpvm_muzzle.json'), 'w'), indent=1)
print('MUZZLE', json.dumps({k: (v['native_cm'], v['slices']) for k, v in OUT.items()})[:3000])
