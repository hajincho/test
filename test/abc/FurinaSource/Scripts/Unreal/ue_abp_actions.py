"""Editor: AnimGraph action names of ABP_Furina matching any argv substring (default: 시퀀스 블렌드 양방향) -> Data/abp_actions.json"""
import unreal, json, sys
def main():
    keys = sys.argv[1:] or ['시퀀스플레이어', '양방향블렌드', '시퀀스이벨', '시퀀스평가', 'SequenceEvaluator', 'SequencePlayer']
    ab = unreal.load_asset('/Game/Furina/ABP_Furina'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(ab, 'AnimGraph')
    acts = [str(a) for a in ed.list_available_nodes([])]
    out = [a for a in acts if any(k in a for k in keys)]
    json.dump(dict(total=len(acts), matches=out[:80]), open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\abp_actions.json', 'w'), indent=1, ensure_ascii=False); print('ABP_ACTIONS', len(acts), len(out))
    del ed, ab
import traceback
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\abp_actions.json', 'w'), indent=1)
