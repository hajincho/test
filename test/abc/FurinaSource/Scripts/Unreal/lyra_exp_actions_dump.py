"""Lyra 에디터(`py <파일>`): 모든 경험의 액션(AddComponents 대상/클래스, AddInputContextMapping, AddInputBinding, AddAbilities 등)과 액션 세트의 액션을 자세히 덤프 -> Data/lyra_exp_actions_dump.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_exp_actions_dump.json'
EXPS = ['/Game/System/Experiences/B_Furina_Experience', '/ShooterCore/Experiences/B_ShooterGame_Elimination', '/TopDownArena/System/Experiences/B_TopDownArenaExperience',
        '/TopDownArena/System/Experiences/B_TopDownArena_Multiplayer_Experience', '/ShooterExplorer/System/Experiences/B_TestInventoryExperience', '/Game/System/Experiences/B_LyraDefaultExperience']
R = {}
def dump_action(a):
    d = {'class': a.get_class().get_name()}
    for n in dir(a):
        if n.startswith('_') or n in ('get_class', 'get_name'): continue
        if any(k in n.lower() for k in ('component', 'target', 'class', 'mapping', 'input', 'widget', 'ability', 'granted', 'priority', 'camera', 'layout', 'binding', 'config')) and not callable(getattr(a, n, None)):
            try: d[n] = str(a.get_editor_property(n))[:400]
            except Exception: pass
    return d
try:
    for p in EXPS:
        try:
            bp = unreal.load_asset(p + '.' + p.rsplit('/', 1)[1]) or unreal.load_asset(p); cdo = unreal.get_default_object(bp.generated_class())
            row = {'pawn': str(cdo.get_editor_property('default_pawn_data')), 'features': str(cdo.get_editor_property('game_features_to_enable')), 'actions': [dump_action(a) for a in cdo.get_editor_property('actions') if a], 'sets': {}}
            for s in cdo.get_editor_property('action_sets'):
                row['sets'][s.get_name()] = {'actions': [dump_action(a) for a in s.get_editor_property('actions') if a], 'features': str(s.get_editor_property('game_features_to_enable'))}
            R[p] = row
        except Exception: R[p] = {'error': traceback.format_exc()[-300:]}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_EXP_ACTIONS', len(R))
