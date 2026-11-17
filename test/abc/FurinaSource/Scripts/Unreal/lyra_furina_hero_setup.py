"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태): 푸리나=플레이어, Lyra 마네킹=봇, 무기 제거 설정.
 A) /Game/Furina/Lyra/AbilitySet_Furina = AbilitySet_ShooterHero 복제 - 무기 어빌리티(GA_QuickbarSlots, GA_ADS, GA_Grenade, GA_DropWeapon, GA_Melee)
 B) /Game/Furina/Lyra/HeroData_Furina: PawnClass = B_Hero_ShooterMannequin(봇/기본 폰), AbilitySets = [AbilitySet_Furina]
 C) /Game/System/Experiences/B_Furina_Experience: 액션 세트에서 StandardComponents(퀵바/장비), StandardHUD(무기 HUD), SharedInput(Lyra 영웅 입력) 제거
 D) /Game/B_LyraGameMode: GetDefaultPawnClassForController 오버라이드 - 사람(PlayerController)이면 푸리나 폰, 아니면 부모(=PawnData 의 마네킹)
 -> Data/lyra_furina_hero_setup.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_hero_setup.json'
R = {'log': []}
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
WEAPON = ('GA_QuickbarSlots', 'GA_ADS', 'GA_Grenade', 'GA_DropWeapon', 'GA_Melee')
FURINA = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def step(name, fn):
    try: R[name] = fn()
    except Exception: R[name] = 'ERROR ' + traceback.format_exc()[-700:]
def A():
    dst = '/Game/Furina/Lyra/AbilitySet_Furina'
    if not EAL.does_asset_exist(dst): assert EAL.duplicate_asset('/ShooterCore/Game/AbilitySet_ShooterHero', dst), 'dup'
    a = unreal.load_asset(dst); lst = list(a.get_editor_property('granted_gameplay_abilities'))
    keep = [x for x in lst if not any(w in x.get_editor_property('ability').get_path_name() for w in WEAPON)]
    a.set_editor_property('granted_gameplay_abilities', keep); ok = EAL.save_loaded_asset(a, False)
    return {'before': len(lst), 'after': len(a.get_editor_property('granted_gameplay_abilities')), 'kept': [x.get_editor_property('ability').get_name() for x in a.get_editor_property('granted_gameplay_abilities')], 'saved': ok}
def B():
    h = unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina')
    h.set_editor_property('pawn_class', unreal.load_class(None, '/ShooterCore/Game/B_Hero_ShooterMannequin.B_Hero_ShooterMannequin_C'))
    h.set_editor_property('ability_sets', [unreal.load_asset('/Game/Furina/Lyra/AbilitySet_Furina')])
    return {'pawn_class': str(h.get_editor_property('pawn_class')), 'ability_sets': [str(x) for x in h.get_editor_property('ability_sets')], 'saved': EAL.save_loaded_asset(h, False)}
def C():
    bp = unreal.load_asset('/Game/System/Experiences/B_Furina_Experience'); cdo = unreal.get_default_object(bp.generated_class())
    sets = list(cdo.get_editor_property('action_sets')); drop = ('LAS_ShooterGame_StandardComponents', 'LAS_ShooterGame_StandardHUD', 'LAS_ShooterGame_SharedInput')
    keep = [x for x in sets if x.get_name() not in drop]; cdo.set_editor_property('action_sets', keep)
    BEL.compile_blueprint(bp); ok = EAL.save_loaded_asset(bp, False)
    return {'before': [x.get_name() for x in sets], 'after': [x.get_name() for x in keep], 'saved': ok}
def D():
    gm = unreal.load_asset('/Game/B_LyraGameMode'); name = 'GetDefaultPawnClassForController'
    g = BEL.add_function_override(gm, name); R['log'].append('override graph: ' + str(g))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(gm, name); nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    info = {n: [str(n_.get_node_title()).replace('\n', ' '), [str(p.get_pin_name()) for p in n_.list_all_pins()]] for n, n_ in nodes.items()}
    R['override_nodes_before'] = info
    entry = next(n for n in nodes.values() if 'FunctionEntry' in n.get_class().get_name()); parent = next((n for n in nodes.values() if 'CallParent' in n.get_class().get_name() or 'Parent:' in str(n.get_node_title())), None)
    result = next(n for n in nodes.values() if 'FunctionResult' in n.get_class().get_name())
    if 'FDG_Branch' not in nodes:
        ctl_pin = next(p for p in entry.list_all_pins() if str(p.get_pin_name()) not in ('then', 'execute') and 'exec' not in str(p.get_pin_name()).lower())
        isp = ed.add_call_function_node('/Script/Engine.Controller:IsPlayerController'); isp.rename('FDG_IsPlayer')
        unreal.BlueprintGraphPinLibrary.try_create_connection(ctl_pin, isp.find_self_pin())
        br = ed.add_branch_node(); br.rename('FDG_Branch')
        unreal.BlueprintGraphPinLibrary.try_create_connection(isp.find_result_pin(), br.find_input_pin('Condition'))
        old = list(entry.find_then_pin().list_connected_pins())
        unreal.BlueprintGraphPinLibrary.try_create_connection(entry.find_then_pin(), br.find_input_pin('execute'))
        if parent is not None: unreal.BlueprintGraphPinLibrary.try_create_connection(br.find_output_pin('else'), parent.find_input_pin('execute'))
        ret2 = ed.add_return_node(); ret2.rename('FDG_Return')
        rv = next(p for p in ret2.list_all_pins() if str(p.get_pin_name()) not in ('execute',))
        rv.set_pin_value(FURINA + '.ThirdPersonCharacter_BP_C')
        unreal.BlueprintGraphPinLibrary.try_create_connection(br.find_output_pin('then'), ret2.find_input_pin('execute'))
        R['log'].append('override graph built')
    BEL.compile_blueprint(gm); R['gm_status'] = str(gm.get_editor_property('status'))
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(gm, name)
    R['override_nodes_after'] = {n.get_name(): [str(n.get_node_title()).replace('\n', ' '), [(str(p.get_pin_name()), str(p.get_pin_value())[:80], [c.get_owning_node().get_name() for c in p.list_connected_pins()]) for p in n.list_all_pins()]] for n in ed.list_all_nodes()}
    return EAL.save_loaded_asset(gm, False)
step('A_ability_set', A); step('B_hero_data', B); step('C_experience', C); step('D_gamemode', D)
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_SETUP done')
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
