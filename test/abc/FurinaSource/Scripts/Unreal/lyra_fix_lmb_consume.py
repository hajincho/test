"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): Direction_IA(레일 방향 전환, 좌클릭)의 consume_input 을 꺼서 같은 좌클릭의 IA_FurinaFireRifle 이 막히지 않게 한다.
(IMC 에서 Direction_IA 가 먼저 나오고 consume_input=True 라 좌클릭을 가로챔 -> 사격 입력이 안 들어옴)   -> Data/lyra_fix_lmb_consume.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_lmb_consume.json'
R = {}
try:
    p = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Actions/Direction_IA'
    ia = unreal.load_asset(p); R['before'] = ia.get_editor_property('consume_input')
    ia.set_editor_property('consume_input', False); R['after'] = ia.get_editor_property('consume_input')
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(ia, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_LMB', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
