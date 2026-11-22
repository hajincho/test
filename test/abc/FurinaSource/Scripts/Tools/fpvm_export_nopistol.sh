#!/bin/bash
# 권총을 뺀 1인칭 다시 내보내기(손가락 정합 작업용, 2026-11-22). A' 와 B 병렬 -> C
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; S=/c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Blender
run(){ echo "== $*"; "$B" -b --python "$@" 2>&1 | grep -E "Error|Traceback|line [0-9]+" | cut -c1-200 | tail -3; }
( for st in export roundclips meshfix zf39 zf41; do run $S/fpvm_kar98k.py -- $st; done; for k in panzerfaust panzerschreck; do run $S/fpvm_launchers.py -- $k export; done ) &
( for st in export roundclips meshfix zf4 magreload; do run $S/fpvm_g43.py -- $st; done; for k in mp40 mp38 stg44; do run $S/fpvm_smg.py -- $k export; done ) &
wait; bash /c/Users/fromj/Downloads/test/test/abc/FurinaSource/Scripts/Tools/fpvm_export_all.sh C; echo NOPISTOL_DONE
