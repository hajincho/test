"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): Lyra /Game/Input/Mappings/IMC_Default 의 액션 중 푸리나 키와 겹치는 것의 consume_input 을 끈다.
이유: IMC_Default(IA_Weapon_Fire 등, 좌클릭) 가 활성이면서 consume_input=True 라 같은 키의 IA_FurinaFireRifle 이 막혀 사격 입력이 안 들어옴.
(Lyra 무기는 이미 게임플레이에서 제거했으므로 이 액션들은 쓰이지 않는다.)  -> Data/lyra_fix_imc_consume.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fix_imc_consume.json'
R = {'changed': []}
WEAPON_IAS = ('IA_Weapon_Fire', 'IA_Weapon_Fire_Auto', 'IA_Weapon_Reload')
FUR_KEYS = {'LeftMouseButton', 'RightMouseButton', 'R', 'V', 'C', 'B', 'One', 'Two', 'LeftShift', 'Z', 'LeftControl', 'Q', 'MouseWheelAxis', 'SpaceBar', 'W', 'A', 'S', 'D', 'Mouse2D'}
try:
    imc = unreal.load_asset('/Game/Input/Mappings/IMC_Default'); seen = set(); R['mappings'] = []
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        k = str(m.get_editor_property('key').get_editor_property('key_name')); ia = m.get_editor_property('action')
        if not ia: continue
        R['mappings'].append([ia.get_name(), k, bool(ia.get_editor_property('consume_input'))])
        if k in FUR_KEYS and ia.get_path_name() not in seen:
            seen.add(ia.get_path_name())
            want = ia.get_name() in WEAPON_IAS  # 이동/시점/점프/앉기/대시는 Lyra 쪽 기본값(True) 유지: 끄면 푸리나 BP 입력과 이중 처리될 수 있음
            if want != (not ia.get_editor_property('consume_input')):
                ia.set_editor_property('consume_input', not want); R['changed'].append(ia.get_name()); R.setdefault('saved', {})[ia.get_name()] = unreal.EditorAssetLibrary.save_loaded_asset(ia, False)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIX_IMC', R.get('changed'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
