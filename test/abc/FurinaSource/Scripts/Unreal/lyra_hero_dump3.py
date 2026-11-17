"""LYRA 에디터(헤드리스): 어빌리티 세트/액션 세트 항목을 필드 이름으로 읽기, B_LyraGameMode/B_ShooterBotSpawner 구조 확인 -> Data/lyra_hero_dump3.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hero_dump3.json'
R = {}
def s(v, n=200):
    t = str(v); return t if len(t) <= n else t[:n] + '...'
def ge(o, name):
    try: return o.get_editor_property(name)
    except Exception as e: return 'ERR ' + s(e, 60)
def name_of(o):
    try: return o.get_path_name() if hasattr(o, 'get_path_name') else s(o)
    except Exception: return s(o)
try:
    a = unreal.load_asset('/ShooterCore/Game/AbilitySet_ShooterHero')
    R['abilities'] = [{'ability': name_of(ge(x, 'ability')), 'level': s(ge(x, 'ability_level')), 'input_tag': s(ge(x, 'input_tag'))} for x in ge(a, 'granted_gameplay_abilities')]
    R['effects'] = [{'effect': name_of(ge(x, 'gameplay_effect')), 'level': s(ge(x, 'effect_level'))} for x in ge(a, 'granted_gameplay_effects')]
    R['attr_sets'] = [name_of(ge(x, 'attribute_set')) for x in ge(a, 'granted_attributes')] if not isinstance(ge(a, 'granted_attributes'), str) else 'n/a'
    def acts(path):
        o = unreal.load_asset(path); out = []
        for x in ge(o, 'actions'):
            d = {'cls': x.get_class().get_name()}
            cl = ge(x, 'component_list')
            if not isinstance(cl, str): d['components'] = [{'actor': name_of(ge(e, 'actor_class')), 'component': name_of(ge(e, 'component_class')), 'client': s(ge(e, 'client_component')), 'server': s(ge(e, 'server_component'))} for e in cl]
            w = ge(x, 'widgets')
            if not isinstance(w, str): d['widgets'] = [{'widget': name_of(ge(e, 'widget_class')), 'slot': s(ge(e, 'slot_id'))} for e in w]
            lay = ge(x, 'layout')
            if not isinstance(lay, str): d['layout'] = [{'layout': name_of(ge(e, 'layout_class')), 'layer': s(ge(e, 'layer_id'))} for e in lay]
            ic = ge(x, 'input_configs')
            if not isinstance(ic, str): d['input_configs'] = [name_of(e) if not hasattr(e, 'get_editor_property') else s(e) for e in ic]
            im = ge(x, 'input_mappings')
            if not isinstance(im, str): d['input_mappings'] = [s(e, 300) for e in im]
            out.append(d)
        return out
    for p in ('LAS_ShooterGame_StandardComponents', 'LAS_ShooterGame_SharedInput', 'LAS_ShooterGame_StandardHUD'): R[p] = acts('/ShooterCore/Experiences/' + p)
    R['EAS_BasicShooterAcolades'] = acts('/ShooterCore/Accolades/EAS_BasicShooterAcolades')
    # B_Furina_Experience 의 자체 액션
    exp = unreal.load_asset('/Game/System/Experiences/B_Furina_Experience'); cdo = unreal.get_default_object(exp.generated_class()); res = []
    for x in ge(cdo, 'actions'):
        d = {'cls': x.get_class().get_name()}
        cl = ge(x, 'component_list')
        if not isinstance(cl, str): d['components'] = [{'actor': name_of(ge(e, 'actor_class')), 'component': name_of(ge(e, 'component_class'))} for e in cl]
        w = ge(x, 'widgets')
        if not isinstance(w, str): d['widgets'] = [{'widget': name_of(ge(e, 'widget_class')), 'slot': s(ge(e, 'slot_id'))} for e in w]
        ab = ge(x, 'abilities_list')
        if not isinstance(ab, str): d['abilities_list'] = [s(e, 300) for e in ab]
        res.append(d)
    R['B_Furina_Experience_actions'] = res
    # 게임 모드 BP 구조
    gm = unreal.load_asset('/Game/B_LyraGameMode'); R['B_LyraGameMode'] = {'parent': s(unreal.BlueprintEditorLibrary.get_blueprint_parent_class(gm)), 'graphs': [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(gm)], 'events': [str(e) for e in unreal.BlueprintEditorLibrary.list_events(gm)] if hasattr(unreal.BlueprintEditorLibrary, 'list_events') else None}
    sp = unreal.load_asset('/ShooterCore/Bot/B_ShooterBotSpawner'); cdo = unreal.get_default_object(sp.generated_class())
    R['BotSpawner'] = {'parent': s(unreal.BlueprintEditorLibrary.get_blueprint_parent_class(sp)), 'num_bots': s(ge(cdo, 'num_bots_to_create')), 'controller': s(ge(cdo, 'bot_controller_class'))}
    R['B_Hero_Default'] = {'graphs': [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(unreal.load_asset('/Game/Characters/Heroes/B_Hero_Default'))]}
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_DUMP3', R.get('error', 'ok')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
