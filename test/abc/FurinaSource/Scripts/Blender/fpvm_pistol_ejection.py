"""blender -b --python fpvm_pistol_ejection.py : 권총 탄피 배출구 위치·방향(2026-11-21, 고증) -> Data/fpvm_pistol_ejection.json
 연구 문서 5-3절: P38 = 슬라이드 '왼쪽' 배출구(왼쪽으로 튐), P08 = 토글이 위로 꺾이며 '위'로 튐(약간 오른쪽·뒤), PP = 슬라이드 오른쪽 배출구(오른쪽으로 튐)
 배출구 = 약실 바로 뒤(총열 뒤끝 + 0.8cm), 총열 축보다 조금 위. 옆으로 튀는 총은 그 높이의 슬라이드 옆면, P08 은 윗면.
 출력: UE 카메라 공간(정조준 자세 = 메시 기준 자세) 위치 cm, 배출 방향(단위), 총 뒤쪽 방향 -> lyra_pistol_cases.py 가 VM_CaseFX 소켓으로"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpvm_lib as L
from fpvm_pistols import visual_top, PISTOL_POS
BARREL_MM = {'p38': 125, 'p08': 100, 'pp': 98}   # Wikipedia 제원(연구 문서 9절)
# 배출 방향(원본 축: 총의 왼쪽 +X, 뒤 +Y, 위 +Z)
EJECT = {'p38': (0.85, 0.25, 0.45), 'p08': (-0.30, 0.35, 0.85), 'pp': (-0.85, 0.25, 0.45)}
OUT = {}
for key in ('p38', 'p08', 'pp'):
    gun = L.load_weapon(key); top = visual_top(gun, key)
    P = np.array([v.co[:] for v in gun.data.vertices]); T = np.array([v.co[:] for v in top.data.vertices]); A_ = np.vstack([P, T])
    ymin = A_[:, 1].min(); breech_y = ymin + BARREL_MM[key] / 10.0; port_y = breech_y + 0.8
    sl = P[P[:, 1] < ymin + 0.3]; bore_z = float((sl[:, 2].min() + sl[:, 2].max()) / 2); bore_x = float((sl[:, 0].min() + sl[:, 0].max()) / 2)
    band = A_[np.abs(A_[:, 1] - port_y) < 0.6]
    if key == 'p08':
        z = float(band[np.abs(band[:, 0] - bore_x) < 0.6][:, 2].max()) + 0.2; native = (bore_x, port_y, z)
    else:
        zz = bore_z + 0.7; side = band[np.abs(band[:, 2] - zz) < 0.5]
        x = float(side[:, 0].max()) + 0.2 if EJECT[key][0] > 0 else float(side[:, 0].min()) - 0.2; native = (x, port_y, zz)
    G = L.gun_native_to_cam(PISTOL_POS, 2.5, 4., -3.); w = G @ Vector(native)
    d = (G.to_3x3() @ Vector(EJECT[key])).normalized(); back = (G.to_3x3() @ Vector((0, 1, 0))).normalized()
    OUT[key] = {'native_cm': [round(c, 2) for c in native], 'bore_z': round(bore_z, 2), 'ue_cam_cm': [w.x * 100, -w.y * 100, w.z * 100], 'ue_dir': [d.x, -d.y, d.z], 'ue_back': [back.x, -back.y, back.z]}
    for o in (gun, top): bpy.data.objects.remove(o)
json.dump(OUT, open(os.path.join(L.D, 'Data', 'fpvm_pistol_ejection.json'), 'w'), indent=1)
print('EJECT', json.dumps(OUT))
