"""에디터(편집 전용): Kar98k 1인칭 메시(Interior/ZF39/ZF41)·애니(Idle/Fire/Reload/Loose1~4) 다시 가져오기(2026-11-21).
 장전 자세를 올려(클립 홈이 화면 아래 끝 -27° -> 약 -15°) 낱발·클립 장전이 화면에 보이게 한 수정분. -> Saved/FPVMK98Refresh.json("done": true)"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_clip
from lyra_fpvm_receiver_import import import_viewmodel, receiver_material
ASSETS = unreal.EditorAssetLibrary; ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
def k98():
    mat = receiver_material(); out = {}
    for suffix, optic in (('Interior', None), ('ZF39', 'kar98k_zf39'), ('ZF41', 'kar98k_zf41')):
        mesh, data = import_viewmodel(ROOT, 'Kar98k', suffix, mat, optic); assert ASSETS.save_loaded_asset(mesh, False); out[mesh.get_name()] = data
    folder = '/Game/Furina/FPVM/Kar98k'; skel = unreal.load_asset(f'{folder}/SK_FPVM_Kar98k_Skeleton')
    for c in ('Idle', 'Fire', 'Reload', 'Loose1', 'Loose2', 'Loose3', 'Loose4'):
        a = import_clip(folder, skel, f'AS_FPVM_Kar98k_{c}'); assert ASSETS.save_loaded_asset(a, False); out[a.get_name()] = round(a.get_play_length(), 3)
    return out
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
try:
    try: R['k98'] = k98()
    except Exception: R['k98'] = 'ERROR ' + traceback.format_exc()[-1500:]
finally:
    unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
R['done'] = True
(ROOT / 'Saved' / 'FPVMK98Refresh.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_K98_REFRESH', json.dumps(R, default=str)[:300])
