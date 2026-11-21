"""에디터: Kar98k ZF41 뷰모델 메시만 다시 가져오기(렌즈 유리를 줄이지 않은 판) + VM_Muzzle 소켓 -> Saved/ZF41Reimport.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_receiver_import import import_viewmodel, receiver_material
import lyra_hist_fx as H
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
try:
    mesh, data = import_viewmodel(ROOT, 'Kar98k', 'ZF41', receiver_material(), 'kar98k_zf41'); assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, False); R['mesh'] = data
    R['socket'] = H.sockets().get('kar98k_zf41')
except Exception: R['error'] = traceback.format_exc()[-1500:]
finally: unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
R['done'] = True; (ROOT / 'Saved' / 'ZF41Reimport.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
