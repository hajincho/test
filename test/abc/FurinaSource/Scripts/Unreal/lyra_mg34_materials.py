"""에디터(편집 전용, 2026-11-22): SK_FPVM_MG34 무기 재질 슬롯(이름이 SM_DE_mg34 와 달라 비었던 것) -> MI_DE_mg34_* 지정"""
import unreal
m = unreal.load_asset('/Game/Furina/FPVM/MG34/SK_FPVM_MG34'); base = '/Game/Furina/Weapons/Germany/mg34/'
MAP = {'mg 34': 'MI_DE_mg34_mg_34', 'mg 34 mag': 'MI_DE_mg34_mg_34_mag', 'p line': 'MI_DE_mg34_p_line'}
slots = list(m.materials); out = {}
for s in slots:
    n = str(s.material_slot_name); key = MAP.get(n) or ('MI_DE_mg34_7_92x57_l' if n.startswith('7') else None)
    if key: s.material_interface = unreal.load_asset(base + key); out[n] = key
m.set_editor_property('materials', slots); print('MG34_MATS', out, unreal.EditorAssetLibrary.save_loaded_asset(m, False))
