"""Lyra 에디터(`py <파일> [강도|remove]`, PIE 중지 상태): 비조준(허리)과 견착 상태에서 한 발 쏠 때마다 화면이 짧게 흔들리는 카메라 셰이크를 넣는다. 정조준(FurinaADS 활성)에서는 흔들지 않는다.
1) /Game/Furina/CameraShakes/CS_FurinaShot (CameraShakeBase 블루프린트, WaveOscillator 패턴: 0.18초, 피치/요/롤 진동)을 만든다/갱신한다. 강도 인자(기본 1.0)는 진폭 배율.
2) ThirdPersonCharacter_BP 의 FurinaRifleShot 체인에서 M4_SetFurinaAmmo 다음(= 실제 발사가 성립한 뒤, 탄약 감소 직후)에 `NOT FurinaADS.IsActive` 분기를 넣고 참일 때 PlayerCameraManager.StartCameraShake(CS_FurinaShot)를 호출한다.
   노드 이름: FPN_ShkNot, FPN_ShkBr, FPN_ShkStart.  `remove`: 분기를 우회시켜 비활성(노드는 남김).   -> Data/lyra_fire_shake.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fire_shake.json'
CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
SHAKE = '/Game/Furina/CameraShakes/CS_FurinaShot'
nums = [a for a in sys.argv[1:] if a.replace('.', '', 1).isdigit()]
GAIN = float(nums[0]) if nums else 1.0
R = {'gain': GAIN}
try:
    # 1) 셰이크 에셋
    if not unreal.EditorAssetLibrary.does_asset_exist(SHAKE):
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.CameraShakeBase)
        unreal.AssetToolsHelpers.get_asset_tools().create_asset('CS_FurinaShot', '/Game/Furina/CameraShakes', unreal.Blueprint, f)
    bp_s = unreal.load_asset(SHAKE); cdo = unreal.get_default_object(bp_s.generated_class())
    pat = unreal.new_object(unreal.WaveOscillatorCameraShakePattern, outer=cdo)
    pat.set_editor_property('duration', 0.18); pat.set_editor_property('blend_in_time', 0.015); pat.set_editor_property('blend_out_time', 0.12)
    for axis, amp, freq in (('pitch', 0.55, 34.0), ('yaw', 0.40, 27.0), ('roll', 0.50, 31.0)):
        o = pat.get_editor_property(axis); o.set_editor_property('amplitude', amp * GAIN); o.set_editor_property('frequency', freq); pat.set_editor_property(axis, o)
    pat.set_editor_property('rotation_amplitude_multiplier', 1.0); pat.set_editor_property('rotation_frequency_multiplier', 1.0); pat.set_editor_property('location_amplitude_multiplier', 0.0); pat.set_editor_property('location_frequency_multiplier', 1.0)
    cdo.set_root_shake_pattern(pat)
    R['pattern'] = str(cdo.get_root_shake_pattern()); R['shake_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp_s)
    # 2) 그래프
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); names = {n.get_name(): n for n in ed.list_all_nodes()}
    if 'FPN_ShkBr' not in names:
        ammo = names['M4_SetFurinaAmmo']; nxt = list(ammo.find_then_pin().list_connected_pins()); assert nxt, 'no next'
        R['next'] = [p.get_owning_node().get_name() for p in nxt]
        ads = names['K2Node_FPF_AdsOnF']; cam = names['K2Node_FPF_CamMgr']
        nt = ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Not_PreBool'); nt.rename('FPN_ShkNot')
        br = ed.add_branch_node(); br.rename('FPN_ShkBr')
        st = ed.add_call_function_node('/Script/Engine.PlayerCameraManager:StartCameraShake'); st.rename('FPN_ShkStart')
        st.find_input_pin('ShakeClass').set_pin_value(SHAKE + '.CS_FurinaShot_C'); st.find_input_pin('Scale').set_pin_value('1.0')
        assert CONN(ads.find_output_pin('ReturnValue'), nt.find_input_pin('A'))
        cond = br.find_condition_pin() if hasattr(br, 'find_condition_pin') else br.find_input_pin('Condition')
        assert CONN(nt.find_output_pin('ReturnValue'), cond)
        assert CONN(cam.find_output_pin('ReturnValue'), st.find_self_pin())
        ammo.find_then_pin().break_pin_links()
        assert CONN(ammo.find_then_pin(), br.find_execute_pin())
        assert CONN(br.find_output_pin('then'), st.find_execute_pin())
        for p in nxt:
            assert CONN(st.find_then_pin(), p); assert CONN(br.find_output_pin('else'), p)
        R['added'] = True
    elif 'remove' in sys.argv:
        R['note'] = 'remove: 노드를 직접 지우지 않음. FPN_ShkBr 조건을 끄려면 강도 0 으로 다시 실행'
    del ed, names
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIRE_SHAKE', R.get('status'), R.get('error', '')[-300:])
