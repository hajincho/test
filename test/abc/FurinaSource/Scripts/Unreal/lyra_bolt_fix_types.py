"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 PIE/다른 블루프린트 스크립트 전에 실행): 노리쇠 변수 FurinaBoltKick/FurinaBoltHold 가 정수로 만들어져 있었다(get_basic_type_by_name('float') 가 정수 타입을 돌려줌).
 1) 두 변수의 타입을 'real'(배정밀도 실수)로 바꾸고
 2) 정수로 굳어 버린 tick 단계 노드(FBT_Kick0 ... FBT_SetVis, FBT_Ammo/FBT_Reloading 등 FBT_ 중 재장전/발사 단계가 아닌 것)를 지운 뒤, FurinaMagUpdate -> (기존 P2_Branch_01989945) 로 실행선을 복구한다.
 이후 `lyra_bolt_graph.py tick` 으로 tick 단계를 다시 만든다.   -> Data/lyra_bolt_fix_types.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bolt_fix_types.json'
KEEP = {'FBT_Ammo2', 'FBT_AmmoLe0b', 'FBT_NotPistol2', 'FBT_EmptyCond', 'FBT_TimeSel', 'FBT_EmptyBr', 'FBT_EmptyMontage', 'FBT_SetKick1'}
R = {}
def main():
    bp = unreal.load_asset(PAWN); BEL = unreal.BlueprintEditorLibrary
    T = BEL.get_basic_type_by_name('real')
    R['change'] = [[n, BEL.change_member_variable_type(bp, n, T)] for n in ('FurinaBoltKick', 'FurinaBoltHold')]
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    tick = [k for k in N if k.startswith('FBT_') and k not in KEEP]; R['remove'] = tick
    if 'FBT_SetVis' in N:
        nxt = list(N['FBT_SetVis'].find_then_pin().list_connected_pins()); ev = N['FMG_Update']
        ev.find_then_pin().break_pin_links()
        for p in nxt: assert unreal.BlueprintGraphPinLibrary.try_create_connection(ev.find_then_pin(), p)
        R['relinked'] = [p.get_owning_node().get_name() for p in nxt]
    ed.remove_nodes([N[k] for k in tick])
    del ed, N, nxt, ev
    return bp
try:
    bp = main()
    import gc; gc.collect()
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    del bp
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BOLT_FIX_TYPES', R.get('status'), R.get('error', '')[-300:])
for _n in ('bp', 'main'): globals().pop(_n, None)
import gc; gc.collect()
