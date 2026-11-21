"""헤드리스: (1) 실수로 켠 엔진 기본 재질 WorldGridMaterial 의 used_with_skeletal_mesh 를 원래(False)로 되돌림
 (2) 뷰모델 SK_FPVM_Kar98k 슬롯 재질을 새 SkeletalMaterial 구조체로 다시 지정(이전 방식은 저장되지 않았음) + 각 MI 의 기본 재질에 스켈레탈 사용 켜기 -> Data/lyra_fpvm_fix2.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; R = {}; EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
def run():
    wg = unreal.load_asset('/Engine/EngineMaterials/WorldGridMaterial'); R['wg_before'] = wg.get_editor_property('used_with_skeletal_mesh')
    if R['wg_before']: wg.set_editor_property('used_with_skeletal_mesh', False); MEL.recompile_material(wg); R['wg_saved'] = bool(EAL.save_loaded_asset(wg, False))
    R['wg_after'] = wg.get_editor_property('used_with_skeletal_mesh')
    imp = json.load(open(D + r'\lyra_fpvm_import_Kar98k.json', encoding='utf-8')); want = {s: p for s, p in imp['slots'] if p}
    sm = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k'); old = sm.get_editor_property('materials'); new = []; R['slots'] = []
    for m in old:
        sl = str(m.get_editor_property('material_slot_name')); p = want.get(sl); mi = unreal.load_asset(p.split('.')[0]) if p else m.get_editor_property('material_interface')
        nm = unreal.SkeletalMaterial(material_interface=mi, material_slot_name=m.get_editor_property('material_slot_name'))
        try: nm.set_editor_property('uv_channel_data', m.get_editor_property('uv_channel_data'))
        except Exception: pass
        new.append(nm); R['slots'].append([sl, mi.get_path_name() if mi else None])
    sm.set_editor_property('materials', new); R['mesh_saved'] = bool(EAL.save_loaded_asset(sm, False))
    R['check'] = [[str(m.get_editor_property('material_slot_name')), m.get_editor_property('material_interface').get_path_name() if m.get_editor_property('material_interface') else None] for m in unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k').get_editor_property('materials')]
    R['bases'] = {}
    for sl, p in R['slots']:
        if not p: continue
        base = unreal.load_asset(p.split('.')[0]).get_base_material(); k = base.get_path_name()
        if k.startswith('/Engine/'): R['bases'][k] = 'engine (skip)'; continue
        if k in R['bases']: continue
        was = base.get_editor_property('used_with_skeletal_mesh'); R['bases'][k] = {'was': was}
        if not was: base.set_editor_property('used_with_skeletal_mesh', True); MEL.recompile_material(base); R['bases'][k]['saved'] = bool(EAL.save_loaded_asset(base, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
json.dump(R, open(D + r'\lyra_fpvm_fix2.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('FPVM_FIX2', R.get('error', '')[-300:])
