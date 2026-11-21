"""헤드리스/에디터(편집 전용, PIE 아님): 1인칭 뷰모델 에셋 전체 다시 가져오기(2026-11-21 현재 상태, Blender 는 Tools/fpvm_export_all.sh 먼저).
 run_ue_probe.ps1 -ScriptPath <이 파일> -Done Saved/FPVMReimport.json 으로 실행 가능("done": true 를 씀). BP 설치는 README '다시 만들기 순서'.
 1) 무기 마스터 재질 M_FurinaWeaponPBR 양면(two-sided): 장전·사격 때 드러나는 부품 안쪽 면이 투명하게 보이던 문제(앞으로 넣는 무기 공통)
 2) 낱발 탄 SM_FPVM_LooseRound 교체(소켓 기준 90° 누워 있던 탄 방향 수정)
 3) Kar98k / G43: 손 위치·소매 접기 반영 메시(Interior, ZF39, ZF41, ZF4) + 애니(Idle/Fire/Reload/LooseN/Clip5)
 4) 권총 P38/P08/PP(fpvm_pistols2.py: 세 자세 + 실제 탄창, 클립 13개) 5) MP40/MP38/StG44 메시 + 애니 6) G43 MagReload(저격용 탄창 교환)
 7) 모든 1인칭 메시에 VM_Muzzle 소켓(메시를 다시 가져오면 소켓이 빠질 수 있어 마지막에 다시 넣음)
 -> Saved/FPVMReimport.json"""
import json, sys, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_fbx, import_clip, import_pistol
from lyra_fpvm_receiver_import import import_viewmodel, receiver_material
import lyra_hist_fx as H
ASSETS = unreal.EditorAssetLibrary; ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
def two_sided():
    m = unreal.load_asset('/Game/Furina/Weapons/Materials/M_FurinaWeaponPBR'); was = m.get_editor_property('two_sided')
    if not was: m.set_editor_property('two_sided', True); unreal.MaterialEditingLibrary.recompile_material(m)
    assert ASSETS.save_loaded_asset(m, False); return {'was': was, 'now': m.get_editor_property('two_sided')}
def loose_round():
    ui = unreal.FbxImportUI(); ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    t = unreal.AssetImportTask(); t.filename = str(ROOT / 'FurinaSource/FBX/FPVM/SM_FPVM_LooseRound.fbx'); t.destination_path = '/Game/Furina/FPVM'; t.destination_name = 'SM_FPVM_LooseRound'
    t.automated = True; t.replace_existing = True; t.options = ui; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    rm = unreal.load_asset('/Game/Furina/FPVM/SM_FPVM_LooseRound')
    for i, slot in enumerate(rm.static_materials):
        rm.set_material(i, unreal.load_asset('/Game/Furina/Weapons/Germany/mauser_clip/MI_DE_mauser_clip_' + ('case' if 'Case' in str(slot.material_slot_name) else '6_5')))
    b = rm.get_bounding_box(); assert ASSETS.save_loaded_asset(rm, False); return [[b.min.x, b.min.y, b.min.z], [b.max.x, b.max.y, b.max.z]]
def rifles():
    mat = receiver_material(); out = {}
    for name, suffix, optic in (('Kar98k', 'Interior', None), ('G43', 'Interior', None), ('Kar98k', 'ZF39', 'kar98k_zf39'), ('Kar98k', 'ZF41', 'kar98k_zf41'), ('G43', 'ZF4', 'g43_zf4')):
        mesh, data = import_viewmodel(ROOT, name, suffix, mat, optic); assert ASSETS.save_loaded_asset(mesh, False); out[mesh.get_name()] = data
    for model, clips in (('Kar98k', ('Idle', 'Fire', 'Reload', 'Loose1', 'Loose2', 'Loose3', 'Loose4')), ('G43', ('Idle', 'Fire', 'Reload', 'MagReload', 'Clip5', 'Loose1', 'Loose2', 'Loose3', 'Loose4', 'Loose6', 'Loose7', 'Loose8', 'Loose9'))):
        folder = '/Game/Furina/FPVM/' + model; skel = unreal.load_asset(f'{folder}/SK_FPVM_{model}_Skeleton')
        for c in clips:
            a = import_clip(folder, skel, f'AS_FPVM_{model}_{c}'); assert ASSETS.save_loaded_asset(a, False); out[a.get_name()] = round(a.get_play_length(), 3)
    return out
def smg(key):
    name = key.upper(); folder = '/Game/Furina/FPVM/' + name; mesh_name = 'SK_FPVM_' + name
    import_fbx(mesh_name + '.fbx', folder, mesh_name, mesh=True, animations=False)
    mesh = unreal.load_asset(folder + '/' + mesh_name); skel = mesh.get_editor_property('skeleton')
    rifle = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k_Interior')
    defaults = {str(s.material_slot_name): s.material_interface for s in rifle.materials}
    for src in ([key] + (['mp38'] if key == 'mp40' else [])):
        props = unreal.load_asset(f'/Game/Furina/Weapons/Germany/{src}/SM_DE_{src}')
        defaults.update({str(s.material_slot_name): s.material_interface for s in props.static_materials})
    mats = []; miss = []
    for slot in mesh.materials:
        m = defaults.get(str(slot.material_slot_name))
        if m: slot.material_interface = m
        else: miss.append(str(slot.material_slot_name))
        mats.append(slot)
    mesh.set_editor_property('materials', mats)
    clips = {c: import_clip(folder, skel, f'AS_FPVM_{name}_{c}') for c in ('Idle', 'Fire', 'Reload')}
    for a in (mesh, skel, *clips.values()): assert ASSETS.save_loaded_asset(a, False), a.get_name()
    return {'mesh': mesh.get_path_name(), 'missing_slots': miss, **{c: round(a.get_play_length(), 3) for c, a in clips.items()}}
def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        for name, fn in (('two_sided', two_sided), ('loose_round', loose_round), ('rifles', rifles),
                         ('pistols', H.pistols), ('smg', lambda: {k: smg(k) for k in ('mp40', 'mp38', 'stg44')}), ('sockets', H.sockets)):
            try: R[name] = fn()
            except Exception: R[name] = 'ERROR ' + traceback.format_exc()[-1500:]
            (ROOT / 'Saved' / 'FPVMReimport.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8')
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))
    R['done'] = True; (ROOT / 'Saved' / 'FPVMReimport.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FPVM_REIMPORT_DONE')
if __name__ == "__main__": main()
