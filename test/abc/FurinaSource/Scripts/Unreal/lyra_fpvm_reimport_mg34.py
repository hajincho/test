"""에디터(편집 전용, 2026-11-23): MG34 1인칭 다시 가져오기(lyra_fpvm_reimport.smg('mg34')) + 무기 재질(lyra_mg34_materials.py) + 총구 소켓(lyra_hist_fx.sockets)
 lyra_fpvm_reimport.py 의 main 은 MG34 를 포함하지 않음(MG34 는 lyra_fpvm_mg34_bp.py 가 처음 넣음). -> Saved/FPVMReimportMG34.json"""
import json, runpy, sys, traceback
from pathlib import Path
import unreal
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import lyra_fpvm_reimport as RI
import lyra_hist_fx as H
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try: R['mg34'] = RI.smg('mg34')
    finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    runpy.run_path(str(HERE / 'lyra_mg34_materials.py')); R['materials'] = True
    R['sockets'] = H.sockets()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'FPVMReimportMG34.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8'); print('REIMPORT_MG34', json.dumps(R, default=str, ensure_ascii=False)[:1500])
