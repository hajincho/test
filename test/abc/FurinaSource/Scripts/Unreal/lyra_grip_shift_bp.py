"""Lyra 에디터(PIE 중지): lyra_grip_shift.py 의 짝. 폰 EventGraph 의 권총<->소총 전환 노드(P2_*)가 매 틱 소총 상대 위치를 리터럴로 다시 넣고 있어서
(MkVec_b425cf20: X 기본값, Y = P2_LitD_9e7e301 + 스왑*(-26), Z = P2_LitD_124d465), 템플릿만 바꾼 값이 런타임에 덮였다.
그 리터럴을 Data/lyra_grip_shift.json 의 new_rifle_loc 로 바꾼다(D=0 으로 lyra_grip_shift.py 를 돌린 뒤 이걸 돌리면 원상 복구). -> Data/lyra_grip_shift_bp.json"""
import unreal, json, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_grip_shift_bp.json'
R = {}
try:
    nl = json.load(open(D_DIR + r'\lyra_grip_shift.json', encoding='utf-8'))['new_rifle_loc']; R['target'] = nl
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def setp(node, pin, val):
        n = [v for k, v in nodes.items() if k.startswith(node)][0]
        p = [x for x in n.list_all_pins() if str(x.get_pin_name()) == pin][0]
        before = str(p.get_pin_value()); p.set_pin_value(repr(float(val))); return [node, pin, before, str(p.get_pin_value()), [c.get_owning_node().get_name() for c in p.list_connected_pins()]]
    R['set'] = [setp('P2_MkVec_b425cf20', 'X', nl[0]), setp('P2_LitD_9e7e301', 'Value', nl[1]), setp('P2_LitD_124d465', 'Value', nl[2]), setp('P2_LitD_200c0416', 'Value', nl[2])]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    try: R['errors'] = [x.get_name()[:40] for x in ed.list_nodes_with_errors()][:10]
    except Exception: pass
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_GRIP_SHIFT_BP', R.get('saved'), R.get('error', '')[-200:])
