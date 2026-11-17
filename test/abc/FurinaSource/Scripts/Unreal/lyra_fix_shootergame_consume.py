"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): /ShooterCore/Input/Mappings/IMC_ShooterGame 의 모든 액션 consume_input 을 끈다.
이유: 이 IMC 가 활성이고 IA_ADS(우클릭), IA_QuickSlot1/2(1·2번)가 consume_input=True 라 푸리나의 IA_FurinaADS/Shoulder/Weapon1/Weapon2 가 막혔다
(견착·정조준·2번 무기(권총) 사라짐). Lyra 무기는 게임플레이에서 이미 빠졌다.   -> Data/lyra_fix_shootergame_consume.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_shootergame_consume.json'
R = {'mappings': [], 'changed': [], 'saved': {}}
try:
    imc = unreal.load_asset('/ShooterCore/Input/Mappings/IMC_ShooterGame'); seen = set()
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        k = str(m.get_editor_property('key').get_editor_property('key_name')); ia = m.get_editor_property('action')
        if not ia: continue
        R['mappings'].append([ia.get_name(), k, bool(ia.get_editor_property('consume_input'))])
        if ia.get_path_name() in seen: continue
        seen.add(ia.get_path_name())
        if ia.get_editor_property('consume_input'):
            ia.set_editor_property('consume_input', False); R['changed'].append(ia.get_name()); R['saved'][ia.get_name()] = unreal.EditorAssetLibrary.save_loaded_asset(ia, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_SG', R.get('changed'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
