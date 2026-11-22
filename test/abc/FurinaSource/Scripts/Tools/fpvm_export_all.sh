#!/bin/bash
# 1인칭 뷰모델 전체 다시 내보내기(Blender, 2026-11-21 현재 상태). 두 줄로 나눠 병렬 실행: bash fpvm_export_all.sh A & bash fpvm_export_all.sh B & wait; bash fpvm_export_all.sh C
#  A: Kar98k(+ZF39/ZF41) + 권총 3종(fpvm_pistols2.py: 세 자세·실제 탄창 재장전) + 판처파우스트·판처슈렉(fpvm_launchers.py)
#  B: G43(+ZF4, 저격용 탄창 교환 magreload) + MP40/MP38/StG44
#  C(A·B 뒤): 낱발 탄, 총구 위치, 정조준 변환, 연기 덩어리(지금은 BP 에서 끔), 사격 효과 수치
# 이어서 언리얼: Scripts/Unreal/lyra_fpvm_reimport.py(에셋) -> README '다시 만들기 순서' 의 BP 설치 스크립트들(한 번만)
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; S=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Blender
T=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Tools; DATA=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Data
run(){ echo "== $*"; "$B" -b --python "$@" 2>&1 | grep -E "Error|Traceback|line [0-9]+|FPVM|SEAT|MUZZLE|SMOKE|LAUNCHER" | cut -c1-200 | tail -3; }
if [ "$1" = A ]; then
  for st in export roundclips meshfix zf39 zf41; do run $S/fpvm_kar98k.py -- $st; done
  for k in p38 p08 pp; do run $S/fpvm_pistols2.py -- $k export; done
  for k in panzerfaust panzerschreck; do run $S/fpvm_launchers.py -- $k export; done   # 대전차 화기(영점별 정조준 -> Data/fpvm_launchers_ads.json)
elif [ "$1" = B ]; then
  for st in export roundclips meshfix zf4 magreload; do run $S/fpvm_g43.py -- $st; done
  run $S/de_mp40_mag.py   # MP40 자체 탄창(원본 MP40.fbx) -> FBX/Weapons/SM_DE_mp40_mag.fbx
  for k in mp40 mp38 stg44; do run $S/fpvm_smg.py -- $k export; done
else
  run $S/fpvm_loose_prop.py
  run $S/fpvm_muzzle_points.py
  run $S/fpvm_pistol_ejection.py   # 권총 탄피 배출구(고증) -> Data/fpvm_pistol_ejection.json
  run $S/fpvm_ads_calc.py -- all
  run $S/fx_smoke_puffs.py
  python $T/gen_hist_fx.py $DATA
fi
echo DONE_$1
