"""blender -b --python fpvm_rifle_ejection.py : Kar98k·G43 탄피 배출구 위치·방향(2026-11-23, 고증) -> Data/fpvm_rifle_ejection.json
 연구 문서 12절: Kar98k(Mauser 98) = 볼트를 끝까지 당길 때 고정 추출기가 탄피를 위-오른쪽으로 튕김(윗면 열린 곳),
                 G43 = 쏠 때 캐리어가 뒤로 가며 오른쪽 배출구로 튕김(오른쪽·조금 위·조금 앞).
 약실 뒤끝(볼트 면): Kar98k = 총구(정리본 원점 = 경계 상자 중심, 전장 111 -> y -55.5) + 총열 600mm = y 4.5,
                     G43 = 닫힌 캐리어 앞면 y 0.35(fpvm_g43.json carrier; 총구 -56.5 + 총열 550mm = -1.5 와 2cm 안).
 원본 무기 FBX(EXP 폴더)가 지금 PC 에 없어 기하 대신 위 수치만 씀.
 배출 순간 탄피 가운데: Kar98k = 볼트 면 + 볼트 행정(8.8) - 탄피 길이 절반(2.85), G43 = 볼트 면 + 2.85(탄피 입구가 약실을 막 벗어남).
 출력: UE 카메라 공간 위치 cm, 배출 방향, 총 앞쪽(탄피 축) 방향 -> lyra_rifle_cases.py 가 VM_CaseFX 소켓으로
 원본 축: 총구 -Y, 위 +Z, 총의 오른쪽 -X"""
import bpy, json, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpvm_lib as L
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Data')
BREECH_Y = {'kar98k': -55.5 + 60.0, 'g43': 0.35}
SIDE_X = {'g43': -1.28 - 0.2}   # 캐리어 오른쪽 면(x -1.28) 밖 0.2
BORE = {'kar98k': (0.65, 6.92), 'g43': (0.0, 5.67)}          # fpvm_kar98k.BOLT_AX, fpvm_g43.BORE
BOLT_TRAVEL = {'kar98k': 8.8, 'g43': 9.3}
EJECT = {'kar98k': (-0.70, 0.15, 0.70), 'g43': (-0.90, -0.10, 0.40)}   # (오른쪽 = -X, 뒤 = +Y, 위 = +Z)
OUT = {}
for key in ('kar98k', 'g43'):
    info = json.load(open(os.path.join(DATA, 'fpvm_%s.json' % key)))
    gpos, grot = info['gun_pos'], info['gun_rot']
    breech = BREECH_Y[key]
    bx, bz = BORE[key]
    cy = breech + (BOLT_TRAVEL[key] - 2.85 if key == 'kar98k' else 2.85)
    if key == 'kar98k':   # 윗면 열린 곳: 볼트 축 바로 위, 조금 오른쪽
        native = (bx - 0.6, cy, bz + 0.9)
    else:                 # 오른쪽 배출구: 총열 축 높이 + 0.5, 캐리어 오른쪽 면 밖
        native = (SIDE_X[key], cy, bz + 0.5)
    G = L.gun_native_to_cam(gpos, *grot); w = G @ Vector(native)
    d = (G.to_3x3() @ Vector(EJECT[key])).normalized(); fwd = (G.to_3x3() @ Vector((0, -1, 0))).normalized()
    OUT[key] = {'native_cm': [round(c, 2) for c in native], 'breech_y': round(breech, 2), 'gun_pos': gpos, 'gun_rot': grot, 'ue_cam_cm': [w.x * 100, -w.y * 100, w.z * 100], 'ue_dir': [d.x, -d.y, d.z], 'ue_fwd': [fwd.x, -fwd.y, fwd.z]}
json.dump(OUT, open(os.path.join(DATA, 'fpvm_rifle_ejection.json'), 'w'), indent=1)
print('EJECT', json.dumps(OUT))
