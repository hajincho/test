"""LYRA 에디터(헤드리스): 푸리나에 Lyra 영웅 기능을 붙이기 위한 구조 조사 -> Data/lyra_hero_dump.json
 - AbilitySet_ShooterHero / HeroData_ShooterGame / B_Hero_ShooterMannequin(컴포넌트) / 액션 세트(LAS_*)의 액션 / B_Furina_Experience 의 액션과 설정
 - LyraCharacter 클래스 정보(블루프린트 가능 여부, 컴포넌트)"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hero_dump.json'
R = {}
def s(v, n=160):
    t = str(v)
    return t if len(t) <= n else t[:n] + '...'
def props(o, skip=('get_', 'set_', 'static_', 'call_', 'cast', 'modify', 'rename', 'is_', 'reset_', 'acquire', 'export', 'import', 'to_', 'copy', 'assign')):
    out = {}
    for p in dir(o):
        if p.startswith('_') or p.startswith(skip): continue
        try:
            v = getattr(o, p)
            if callable(v): continue
            out[p] = s(v)
        except Exception: pass
    return out
def load(p):
    try: return unreal.load_asset(p)
    except Exception as e: return None
try:
    # 어빌리티 세트
    a = load('/ShooterCore/Game/AbilitySet_ShooterHero')
    if a:
        row = {}
        for pn in ('granted_gameplay_abilities', 'granted_gameplay_effects', 'granted_attribute_sets'):
            try:
                lst = a.get_editor_property(pn); row[pn] = [s(x.to_dict() if hasattr(x, 'to_dict') else x, 220) for x in lst]
            except Exception as e: row[pn] = 'ERR ' + s(e)
        R['AbilitySet_ShooterHero'] = row
    # 영웅 데이터
    h = load('/ShooterCore/Game/HeroData_ShooterGame')
    if h:
        row = {}
        for pn in ('pawn_class', 'ability_sets', 'tag_relationship_mapping', 'input_config', 'default_camera_mode'):
            try: row[pn] = s(h.get_editor_property(pn))
            except Exception as e: row[pn] = 'ERR ' + s(e)
        R['HeroData_ShooterGame'] = row
    # 영웅 폰 BP 컴포넌트
    bp = load('/ShooterCore/Game/B_Hero_ShooterMannequin')
    if bp:
        S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; comps = []
        for hh in S.k2_gather_subobject_data_for_blueprint(bp):
            d = L.get_data(hh); o = L.get_associated_object(d); comps.append([str(L.get_variable_name(d)), o.get_class().get_name() if o else None])
        R['B_Hero_ShooterMannequin_components'] = comps
        try: R['B_Hero_parent'] = s(bp.generated_class().get_super_struct() if hasattr(bp.generated_class(), 'get_super_struct') else bp.get_editor_property('parent_class'))
        except Exception as e: R['B_Hero_parent'] = 'ERR ' + s(e)
    # 액션 세트와 경험
    def actions_of(path):
        o = load(path)
        if o is None: return 'NOT LOADED'
        try: acts = o.get_editor_property('actions')
        except Exception:
            try: acts = unreal.get_default_object(o.generated_class()).get_editor_property('actions')
            except Exception as e: return 'ERR ' + s(e)
        return [dict(cls=x.get_class().get_name(), **props(x)) for x in acts if x]
    for p in ('LAS_ShooterGame_StandardComponents', 'LAS_ShooterGame_SharedInput', 'LAS_ShooterGame_StandardHUD'):
        R[p] = actions_of('/ShooterCore/Experiences/' + p)
    exp = load('/Game/System/Experiences/B_Furina_Experience')
    if exp:
        cdo = unreal.get_default_object(exp.generated_class()); row = {}
        for pn in ('default_pawn_data', 'game_features_to_enable', 'action_sets', 'actions'):
            try:
                v = cdo.get_editor_property(pn); row[pn] = [s(x) for x in v] if hasattr(v, '__iter__') and not isinstance(v, str) else s(v)
            except Exception as e: row[pn] = 'ERR ' + s(e)
        R['B_Furina_Experience'] = row
    # 액션 세트가 아닌 경험 자체 액션 속성
    try:
        acts = unreal.get_default_object(exp.generated_class()).get_editor_property('actions')
        R['B_Furina_Experience_actions'] = [dict(cls=x.get_class().get_name(), **props(x)) for x in acts if x]
    except Exception as e: R['B_Furina_Experience_actions'] = 'ERR ' + s(e)
    R['LyraCharacter'] = {'path': s(unreal.find_object(None, '/Script/LyraGame.LyraCharacter')), 'has': [c for c in ('LyraCharacter', 'LyraPawnExtensionComponent', 'LyraHealthComponent', 'LyraHeroComponent', 'LyraCameraComponent', 'LyraAbilitySystemComponent') if hasattr(unreal, c)]}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_DUMP', R.get('error', 'ok')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
