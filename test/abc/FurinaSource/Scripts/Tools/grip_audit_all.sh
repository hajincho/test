#!/bin/bash
# 1인칭 손-총 정합 전체 측정(2026-11-22): 무기 10종 × 손 메시 15개(푸리나 Body + 병과 14종 Arms_*) 대기 자세, 8개 병렬.
#  -> Data/grip_audit_<SK>__<클립>__<손>.json, 요약 Data/grip_audit_summary.json (python grip_audit_summary.py)
#  render 붙이면 손마다 6방향 사진도(Data/audit_<SK>_<손>_<R|L>_<방향>.png)
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; S=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Blender
PAIRS="${PAIRS_OVERRIDE:-Kar98k:Kar98k_Idle G43:G43_Idle MP40:MP40_Idle MP38:MP38_Idle STG44:STG44_Idle P38:P38_IdleA P08:P08_IdleA PP:PP_IdleA PANZERFAUST:PANZERFAUST_Idle PANZERSCHRECK:PANZERSCHRECK_Idle}"
HANDS="Body Arms_Infantry Arms_Officer Arms_Assault Arms_AntiTank Arms_Heavy Arms_Sniper Arms_Armor Arms_JpInfantry Arms_JpOfficer Arms_JpAssault Arms_JpAntiTank Arms_JpHeavy Arms_JpSniper Arms_JpArmor"
for p in $PAIRS; do for h in $HANDS; do
  while [ "$(jobs -r | wc -l)" -ge 8 ]; do wait -n; done
  ( "$B" -b --python $S/fpvm_grip_audit.py -- ${p%%:*} ${p##*:} hand=$h frames=3 $1 2>&1 | grep -E "GRIP_AUDIT|Error" | cut -c1-200 ) &
done; done; wait; echo AUDIT_ALL_DONE
