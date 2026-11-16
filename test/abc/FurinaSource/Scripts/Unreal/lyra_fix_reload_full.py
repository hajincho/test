"""Lyra 에디터(`py <파일> keep`): 가득 찬 탄창(20/20)에서도 재장전되던 버그. 재장전 허용 조건 M4_NotFull(잔탄 < N) 의 N 이 예전 30발 탄창 값(30)으로 남아 있었다 -> 20.
-> Data/lyra_fix_reload_full.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_reload_full.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    nf = nodes['M4_NotFull']; pin = nf.find_input_pin('B'); R['before'] = pin.get_pin_value()
    pin.set_pin_value('20'); R['after'] = pin.get_pin_value()
    # 같은 이름의 다른 30 상수가 더 있는지 (참고)
    R['other_30'] = [n.get_name() + ':' + str(n.get_node_title()).replace('\n', ' ') for n in nodes.values() if any(str(p.get_pin_value()) == '30' for p in n.list_all_pins())][:10]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status')); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_RELOAD_FULL', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
