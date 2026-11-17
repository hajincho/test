"""ABP_Furina: Control Rig Alpha 를 항상 1 로 복원 (팔은 CR 의 총 쥐기 IK 사용). 다리/이동은 권총 블렌드스페이스 유지. 컴파일 직후 저장."""
import unreal, json, traceback
abp = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(abp, 'AnimGraph'); R = {}
try:
    assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'PIE running'
    cr = next(n for n in ed.list_all_nodes() if n.get_name() == 'AnimGraphNode_ControlRig_0'); al = cr.find_input_pin('Alpha')
    R['before'] = [c.get_owning_node().get_name()[:30] for c in al.list_connected_pins()]
    al.break_pin_links(); al.set_pin_value('1.0'); R['alpha'] = str(al.get_pin_value())
    unreal.BlueprintEditorLibrary.compile_blueprint(abp); R['status'] = str(abp.get_editor_property('status'))
    if abp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = unreal.EditorAssetLibrary.save_asset('/Game/Furina/ABP_Furina', False)
except Exception: R['error'] = traceback.format_exc()[-800:]
print('P220_CR_RESTORE', json.dumps(R, default=str, ensure_ascii=False))
