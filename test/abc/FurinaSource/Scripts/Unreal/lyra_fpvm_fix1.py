"""헤드리스: (1) 무기 마스터 재질 M_FurinaWeaponPBR 에 '스켈레탈 메시에 사용' 켜기(뷰모델이 기본 회색 재질로 보이던 문제), 팔 재질 부모도 확인
 (2) 캐릭터 BP 의 정조준 변환(VM_AdsB_* MakeTransform) 을 Data/fpvm_kar98k_ads.json 값으로 갱신(눈-뒤가늠자 43cm: 볼트 덮개가 눈앞에 오던 문제) -> Data/lyra_fpvm_fix1.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'; R = {}
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'; BEL = unreal.BlueprintEditorLibrary; MEL = unreal.MaterialEditingLibrary
def run():
    sm = unreal.load_asset('/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k'); R['parents'] = {}
    for m in sm.get_editor_property('materials'):
        mi = m.get_editor_property('material_interface'); base = mi.get_base_material() if mi else None
        if base is None: continue
        k = base.get_path_name()
        if k not in R['parents']:
            was = base.get_editor_property('used_with_skeletal_mesh'); R['parents'][k] = {'was': was}
            if not was:
                base.set_editor_property('used_with_skeletal_mesh', True); MEL.recompile_material(base); R['parents'][k]['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(base, False))
    A = json.load(open(D + r'\fpvm_kar98k_ads.json')); q = A['ue_quat_xyzw']; l = A['ue_loc_cm']; rot = unreal.Quat(q[0], q[1], q[2], q[3]).rotator()
    bp = unreal.load_asset(PAWN); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = [n for n in ed.list_all_nodes() if n.get_name().startswith('VM_AdsB_')]; R['ads_nodes'] = [n.get_name() for n in nodes]
    for n in nodes:
        n.find_input_pin('Location').set_pin_value('%.6f,%.6f,%.6f' % (l[0], l[1], l[2])); n.find_input_pin('Rotation').set_pin_value('%.6f,%.6f,%.6f' % (rot.pitch, rot.yaw, rot.roll))
        R['ads_set'] = [str(n.find_input_pin('Location').get_pin_value()), str(n.find_input_pin('Rotation').get_pin_value())]
    del ed
    import gc; gc.collect()
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
try: run()
except Exception: R['error'] = traceback.format_exc()[-1200:]
json.dump(R, open(D + r'\lyra_fpvm_fix1.json', 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('FPVM_FIX1', R.get('error', '')[-300:])
