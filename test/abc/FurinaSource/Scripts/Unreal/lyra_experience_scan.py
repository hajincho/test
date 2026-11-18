"""Lyra 에디터(`py <파일>`): 모든 LyraExperienceDefinition / LyraExperienceActionSet / LyraUserFacingExperienceDefinition(맵-경험 연결)을 읽어 기본 폰 데이터, 켜는 게임 피처, 액션 목록(클래스 + 핵심 속성)을 덤프
-> Data/lyra_experience_scan.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_experience_scan.json'
R = {'experiences': {}, 'action_sets': {}, 'playlists': {}}
AR = unreal.AssetRegistryHelpers.get_asset_registry()
def s(v, n=160):
    try:
        if hasattr(v, 'get_path_name'): return v.get_path_name()
    except Exception: pass
    return str(v)[:n]
def props(o, names):
    d = {}
    for n in names:
        try: d[n] = s(o.get_editor_property(n))
        except Exception: pass
    return d
def dump_action(a):
    row = {'class': a.get_class().get_name()}
    for n in ('input_mappings', 'input_mapping', 'actors_to_spawn', 'widgets', 'layout', 'extension', 'abilities_list', 'attributes_list', 'components_list', 'bind_actions', 'actions_to_add', 'default_input_mappings'):
        try:
            v = a.get_editor_property(n)
            if isinstance(v, (list, tuple)) or hasattr(v, '__iter__') and not isinstance(v, str):
                row[n] = [s(x) for x in list(v)[:10]]
            else: row[n] = s(v)
        except Exception: pass
    return row
try:
    EXPS = ['/Game/System/Experiences/B_Furina_Experience', '/Game/System/Experiences/B_LyraDefaultExperience', '/Game/System/FrontEnd/B_LyraFrontEnd_Experience',
            '/ShooterCore/Experiences/B_LyraShooterGame_ControlPoints', '/ShooterCore/Experiences/B_ShooterGame_Elimination', '/ShooterCore/Experiences/B_ShooterGame_Perf',
            '/ShooterExplorer/System/Experiences/B_TestInventoryExperience', '/TopDownArena/System/Experiences/B_TopDownArenaExperience', '/TopDownArena/System/Experiences/B_TopDownArena_Multiplayer_Experience']
    SETS = ['/ShooterCore/Experiences/LAS_ShooterGame_SharedInput', '/ShooterCore/Experiences/LAS_ShooterGame_StandardComponents', '/ShooterCore/Experiences/LAS_ShooterGame_StandardHUD', '/ShooterExplorer/System/Experiences/LAS_InventoryTest']
    def assets(cls_path):
        class A:
            def __init__(s2, p): s2.package_name = p; s2.p = p
            def get_asset(s2):
                o = unreal.load_asset(s2.p + '.' + s2.p.rsplit('/', 1)[1])
                if o is None: o = unreal.load_asset(s2.p)
                return o
        return [A(p) for p in (EXPS if cls_path == 'LyraExperienceDefinition' else SETS if cls_path == 'LyraExperienceActionSet' else [])] if cls_path != 'LyraUserFacingExperienceDefinition' else [a for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/LyraGame', cls_path), True)]
    for a in assets('LyraExperienceDefinition'):
        pkg = str(a.package_name)
        try:
            obj = a.get_asset(); cdo = unreal.get_default_object(obj.generated_class()) if hasattr(obj, 'generated_class') else obj
        except Exception as e: R['experiences'][pkg] = {'err': str(e)[:100]}; continue
        row = props(cdo, ['default_pawn_data', 'game_features_to_enable', 'action_sets'])
        row['actions'] = []
        try:
            for ac in cdo.get_editor_property('actions'):
                if ac is not None: row['actions'].append(dump_action(ac))
        except Exception as e: row['actions_err'] = str(e)[:80]
        R['experiences'][pkg] = row
    for a in assets('LyraExperienceActionSet'):
        pkg = str(a.package_name)
        try:
            obj = a.get_asset(); row = props(obj, ['game_features_to_enable']); row['actions'] = []
            for ac in obj.get_editor_property('actions'):
                if ac is not None: row['actions'].append(dump_action(ac))
            R['action_sets'][pkg] = row
        except Exception as e: R['action_sets'][pkg] = {'err': str(e)[:100]}
    for a in assets('LyraUserFacingExperienceDefinition'):
        pkg = str(a.package_name)
        try:
            obj = a.get_asset(); R['playlists'][pkg] = props(obj, ['experience_id', 'map_id', 'extra_args'])
        except Exception as e: R['playlists'][pkg] = {'err': str(e)[:100]}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_EXP_SCAN', len(R['experiences']), len(R['action_sets']), len(R['playlists']), R.get('error', '')[-200:])
