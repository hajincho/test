"""Lyra 에디터(`py <파일> keep`): 푸리나 입력 매핑(IMC)별 액션-키 목록 -> Data/lyra_keys_dump.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_keys_dump.json'
R = {}
try:
    for p in ('/Game/Furina/Input/IMC_FurinaStance', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'):
        imc = unreal.load_asset(p); rows = []
        for m in imc.get_editor_property('mappings'):
            rows.append([m.get_editor_property('action').get_name() if m.get_editor_property('action') else None, str(m.get_editor_property('key').get_editor_property('key_name'))])
        R[p.split('/')[-1]] = rows
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_KEYS_DUMP', R.get('error', 'ok')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
