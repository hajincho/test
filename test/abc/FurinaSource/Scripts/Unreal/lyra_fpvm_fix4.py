"""헤드리스: 뷰모델 메시 교체(VW_Mesh_*) 직후 슬롯 0~9 재질 덮어쓰기를 None 으로(SetMaterial) -> 시작 때 프로젝트가 모든 메시 컴포넌트에 만든 동적 재질(MID, Kar98k 재질)이 G43 에도 남던 문제.
 (UE5.8 은 EmptyOverrideMaterials 가 블루프린트에 없음) -> Data/lyra_fpvm_fix4.json"""
import unreal, json, traceback, time
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'; R = {'added': []}; TOK = '%x' % (int(time.time()) % 0xFFFFF)
CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
try:
    bp = unreal.load_asset(PAWN); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    for i, n in enumerate([n for n in ed.list_all_nodes() if n.get_name().startswith('VW_Mesh_')]):
        nxt = list(n.find_then_pin().list_connected_pins()); n.find_then_pin().break_pin_links()
        prev = n.find_then_pin()
        for k in range(10):
            e = ed.add_call_function_node('/Script/Engine.PrimitiveComponent:SetMaterial'); e.rename('VW_ClrMat_%d_%d_%s' % (i, k, TOK)); e.find_input_pin('ElementIndex').set_pin_value(str(k))
            g = ed.add_get_member_variable_node('FurinaFPVM'); g.rename('VW_ClrMatG_%d_%d_%s' % (i, k, TOK))
            assert CONN(g.find_output_pin('FurinaFPVM'), e.find_self_pin()); assert CONN(prev, e.find_execute_pin()); prev = e.find_then_pin()
        for p in nxt: assert CONN(prev, p)
        R['added'].append([n.get_name(), [p.get_owning_node().get_name() for p in nxt]])
    del ed
    import gc; gc.collect()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fpvm_fix4.json', 'w'), indent=1, default=str); print('FIX4', R)
