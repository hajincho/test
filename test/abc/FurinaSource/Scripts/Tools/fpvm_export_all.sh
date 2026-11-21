#!/bin/bash
# 1인칭 뷰모델 전체 다시 내보내기(손 위치·소매·권총 높이 수정 후). 두 줄로 나눠 병렬 실행: bash fpvm_export_all.sh A|B
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; S=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Blender
run(){ echo "== $*"; "$B" -b --python "$@" 2>&1 | grep -E "Error|Traceback|line [0-9]+|FPVM|SEAT" | cut -c1-200 | tail -3; }
if [ "$1" = A ]; then
  for st in export roundclips meshfix zf39 zf41; do run $S/fpvm_kar98k.py -- $st; done
  for k in p38 p08 pp; do run $S/fpvm_pistols.py -- $k; done
else
  for st in export roundclips meshfix zf4; do run $S/fpvm_g43.py -- $st; done
  for k in mp40 mp38 stg44; do run $S/fpvm_smg.py -- $k export; done
  run $S/fpvm_loose_prop.py
fi
echo DONE_$1
