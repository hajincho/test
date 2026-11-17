"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 왼쪽 Shift 를 푸리나의 원래 달리기(IA_FurinaSprint)로 되돌린다.
Lyra 대시(IA_Ability_Dash, LeftShift, consume_input=True)와 AbilitySet_Furina 의 대시 어빌리티가 Shift 를 가로채고 있었다.
 1) AbilitySet_Furina 에서 대시 어빌리티 제거  2) IA_Ability_Dash consume_input=False   -> Data/lyra_sprint_restore.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_sprint_restore.json'
R = {}
try:
    a = unreal.load_asset('/Game/Furina/Lyra/AbilitySet_Furina'); lst = list(a.get_editor_property('granted_gameplay_abilities'))
    R['before'] = [x.get_editor_property('ability').get_name() for x in lst]
    keep = [x for x in lst if 'Dash' not in x.get_editor_property('ability').get_path_name()]
    a.set_editor_property('granted_gameplay_abilities', keep)
    R['after'] = [x.get_editor_property('ability').get_name() for x in a.get_editor_property('granted_gameplay_abilities')]
    R['set_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(a, False)
    ia = unreal.load_asset('/Game/Input/Actions/IA_Ability_Dash'); R['dash_consume_before'] = ia.get_editor_property('consume_input')
    ia.set_editor_property('consume_input', False); R['ia_saved'] = unreal.EditorAssetLibrary.save_loaded_asset(ia, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SPRINT', R)
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
