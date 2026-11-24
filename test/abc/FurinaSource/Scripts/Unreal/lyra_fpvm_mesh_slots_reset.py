"""에디터(편집 전용, 2026-11-23): 1인칭 메시(SK_FPVM_*) 재질 슬롯을 FBX 기준으로 새로 만들며 메시만 다시 가져오기 -> Saved/FPVMSlotsReset.json
 이유: 캐릭터 통일(Sparxie)로 팔 재질이 Furina_*/CA<병과>_* -> CASparxie_* 로 바뀌었는데, 언리얼이 다시 가져올 때 예전 슬롯 목록을 번호대로 그대로 남김
       (슬롯 이름이 예전 것이라 팔이 안 보이거나 무기 부품 재질이 어긋날 수 있음).
 방법: 메시마다 (예전 슬롯 이름 -> 재질) 기록 -> 슬롯 목록 비움 -> 메시만 다시 가져옴(애니는 그대로) -> 같은 이름 슬롯은 예전 재질 그대로, 새 이름은 무기 원본 재질.
 이어서 돌릴 것: lyra_hist_fx 소켓(VM_Muzzle), lyra_launchers sockets, lyra_mg34_materials, lyra_pzf60_material, lyra_class_fp_arms2 slots, lyra_pistol_cases, lyra_rifle_cases(socket)"""
import json, sys, traceback
from pathlib import Path
import unreal
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import importlib, lyra_fpvm_animation_import as AI, lyra_fpvm_receiver_import as RCV
for _m in (AI, RCV): importlib.reload(_m)
ROOT = Path(unreal.Paths.project_dir()).resolve(); OUTP = ROOT / 'Saved' / 'FPVMSlotsReset.json'
R = json.loads(OUTP.read_text(encoding='utf-8')) if OUTP.exists() else {}
ASSETS = unreal.EditorAssetLibrary
RIFLES = [('Kar98k', 'Interior', None), ('Kar98k', 'ZF39', 'kar98k_zf39'), ('Kar98k', 'ZF41', 'kar98k_zf41'), ('G43', 'Interior', None), ('G43', 'ZF4', 'g43_zf4')]
OTHERS = [('P38', 'p38'), ('P08', 'p08'), ('PP', 'pp'), ('MP40', 'mp40'), ('MP38', 'mp38'), ('STG44', 'stg44'), ('MG34', 'mg34'), ('PANZERFAUST', 'panzerfaust'), ('PANZERSCHRECK', 'panzerschreck')]


def reset(path, do_import, src_keys=()):
    old = unreal.load_asset(path); prev = {str(s.material_slot_name): s.material_interface for s in old.materials}
    old.set_editor_property('materials', []); old.modify()
    do_import()
    m = unreal.load_asset(path); defaults = {}
    for k in src_keys:
        sm = unreal.load_asset(f'/Game/Furina/Weapons/Germany/{k}/SM_DE_{k}')
        if sm: defaults.update({str(s.material_slot_name): s.material_interface for s in sm.static_materials})
    slots = list(m.materials); empty = []
    for s in slots:
        n = str(s.material_slot_name); mi = prev.get(n) or s.material_interface or defaults.get(n)
        if mi: s.material_interface = mi
        else: empty.append(n)
    m.set_editor_property('materials', slots); assert ASSETS.save_loaded_asset(m, False)
    return {'slots': [str(s.material_slot_name) for s in slots], 'empty': empty}


world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    mat = RCV.receiver_material()
    for name, suffix, optic in RIFLES:
        key = f'SK_FPVM_{name}_{suffix}'
        if R.get(key, {}).get('ok'): continue
        try: R[key] = {**reset(f'/Game/Furina/FPVM/{name}/{key}', lambda: RCV.import_viewmodel(ROOT, name, suffix, mat, optic), (name.lower(), 'mauser_clip') + ((optic,) if optic else ())), 'ok': True}
        except Exception: R[key] = {'error': traceback.format_exc()[-800:]}
        OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
    for name, src in OTHERS:
        key = f'SK_FPVM_{name}'
        if R.get(key, {}).get('ok'): continue
        folder = f'/Game/Furina/FPVM/{name}'
        try: R[key] = {**reset(f'{folder}/{key}', lambda: AI.import_fbx(key + '.fbx', folder, key, mesh=True, animations=False),
                                (src,) + (('mp38',) if src == 'mp40' else ()) + (('panzerschreck_rocket',) if src == 'panzerschreck' else ())), 'ok': True}
        except Exception: R[key] = {'error': traceback.format_exc()[-800:]}
        OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
finally:
    unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
R['done'] = True; OUTP.write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
print('SLOTS_RESET', json.dumps({k: (v.get('empty') if isinstance(v, dict) else v) for k, v in R.items()}, ensure_ascii=False)[:2500])
