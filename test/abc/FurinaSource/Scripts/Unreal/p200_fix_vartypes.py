"""float 로 만든 변수가 int 로 생성된 문제 수정: real 타입 새 변수를 만들고 참조를 교체 (노드 재생성 없이)."""
import unreal, json, traceback
BEL = unreal.BlueprintEditorLibrary
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
bp = unreal.load_asset(P); R = {}
try:
    t = BEL.get_basic_type_by_name('real')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    for old in ('FurinaSlideCur', 'FurinaSwapCur', 'FurinaSwapTarget'):
        new = old + 'F'
        R['add_' + new] = BEL.add_member_variable(bp, new, t)
        R['replace_' + old] = str(BEL.replace_variable_references(bp, old, new))
    BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
    R['pawn_vars'] = [str(x) for x in BEL.list_member_variable_names(bp) if 'Slide' in str(x) or 'Swap' in str(x)]
except Exception: R['error'] = traceback.format_exc()[-900:]
print('P200_FIXVAR', json.dumps(R, default=str, ensure_ascii=False))
