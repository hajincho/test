"""Lyra 에디터: 좌클릭에 묶인 액션들(IA_FurinaFireRifle, Direction_IA)의 소비/트리거/모디파이어 -> Data/lyra_ia_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_ia_dump.json'
R = {}
try:
    for p in ('/Game/Furina/Input/IA_FurinaFireRifle', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Direction_IA', '/Game/Furina/Input/IA_FurinaViewToggle'):
        ia = unreal.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None
        if not ia: R[p] = 'missing'; continue
        row = {}
        for n in ('consume_input', 'trigger_when_paused', 'value_type', 'triggers', 'modifiers', 'consumes_action_and_axis_mappings', 'reserve_all_mappings'):
            try: row[n] = str(ia.get_editor_property(n))[:200]
            except Exception as e: row[n] = 'n/a'
        R[p.split('/')[-1]] = row
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    rows = []
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        a = m.get_editor_property('action')
        if str(m.get_editor_property('key').get_editor_property('key_name')) == 'LeftMouseButton':
            row = {'action': a.get_name() if a else None, 'path': a.get_path_name() if a else None, 'triggers': str(m.get_editor_property('triggers'))[:200], 'modifiers': str(m.get_editor_property('modifiers'))[:200]}
            for n in ('consume_input', 'trigger_when_paused', 'value_type', 'triggers', 'modifiers'):
                try: row['ia_' + n] = str(a.get_editor_property(n))[:200]
                except Exception: row['ia_' + n] = 'n/a'
            rows.append(row)
    R['lmb_mappings'] = rows
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_IA_DUMP', R.get('error', 'ok')[-200:])
