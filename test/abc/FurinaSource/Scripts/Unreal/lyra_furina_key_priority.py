"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 키 중복은 푸리나가 우선.
 (1) 푸리나 IMC(Default_IMC, IMC_FurinaStance)의 우선순위를 1000 / 1100 으로 올린다: 폰의 LyraHeroComponent DefaultInputMappings 와 EventGraph 의 AddMappingContext 노드(K2Node_CallFunction_7, TFP_AddStanceContext) 둘 다.
     (Enhanced Input 은 우선순위 높은 IMC 부터 처리한다. 스테이지가 다른 IMC 를 더해도(우선순위 0~수십) 푸리나 매핑이 항상 앞선다.)
 (2) 푸리나가 쓰는 키(푸리나 IMC 의 모든 키)를 같이 쓰는 비푸리나 IMC(Lyra IMC_Default, IMC_ADS_Speed, IMC_ShooterGame, IMC_ShooterGame_KBM, IMC_InventoryTest ...)의 입력 액션은 consume_input=False 로 바꾼다
     (consume 이 켜진 낮은 우선순위 액션이 같은 키를 가로채는 문제. 우선순위가 높아도 낮은 쪽이 consume 이 아니면 둘 다 발동하지만 Lyra 쪽 액션에는 무기/퀵바 등 연결된 것이 없어 무해하다).
 -> Data/lyra_furina_key_priority.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_key_priority.json'
P = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
FUR_IMCS = [('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC', 1000), ('/Game/Furina/Input/IMC_FurinaStance', 1100)]
OTHER = ['/Game/Input/Mappings/IMC_Default', '/ShooterCore/Input/Mappings/IMC_ADS_Speed', '/ShooterCore/Input/Mappings/IMC_ShooterGame', '/ShooterCore/Input/Mappings/IMC_ShooterGame_KBM', '/ShooterExplorer/Input/Mappings/IMC_InventoryTest']
R = {}
EAL = unreal.EditorAssetLibrary
def maps(imc):
    out = []
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        a = m.get_editor_property('action'); out.append((a, str(m.get_editor_property('key').get_editor_property('key_name'))))
    return out
try:
    fkeys = set(); fur_actions = set()
    for path, _ in FUR_IMCS:
        for a, k in maps(unreal.load_asset(path)): fkeys.add(k); fur_actions.add(a.get_name() if a else None)
    R['furina_keys'] = sorted(fkeys)
    # (2) consume
    changed = {}; report = {}
    for path in OTHER:
        imc = unreal.load_asset(path)
        if imc is None: report[path] = 'missing'; continue
        rows = []
        for a, k in maps(imc):
            if a is None: continue
            hit = k in fkeys; was = bool(a.get_editor_property('consume_input')); rows.append([a.get_name(), k, 'shared' if hit else '-', was])
            if hit and was and a.get_name() not in changed:
                a.set_editor_property('consume_input', False); changed[a.get_name()] = bool(EAL.save_loaded_asset(a, False))
        report[path.rsplit('/', 1)[1]] = rows
    R['mappings'] = report; R['changed'] = changed
    # (1) priority: hero component
    bp = unreal.load_asset(P); S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary; comp = None
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h))
        if isinstance(o, unreal.LyraHeroComponent): comp = o
    entries = []
    for path, prio in FUR_IMCS:
        e = unreal.InputMappingContextAndPriority(); e.set_editor_property('input_mapping', unreal.load_asset(path)); e.set_editor_property('priority', prio); entries.append(e)
    comp.set_editor_property('default_input_mappings', entries)
    R['hero_after'] = [x.get_editor_property('input_mapping').get_name() + ' p' + str(x.get_editor_property('priority')) for x in comp.get_editor_property('default_input_mappings')]
    # EventGraph AddMappingContext 노드의 우선순위 핀
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); nodes = {n.get_name(): n for n in ed.list_all_nodes()}; R['nodes'] = {}
    for nm, prio in (('K2Node_CallFunction_7', FUR_IMCS[0][1]), ('TFP_AddStanceContext', FUR_IMCS[1][1])):
        n = nodes.get(nm)
        if n is None: R['nodes'][nm] = 'missing'; continue
        pin = [p for p in n.list_all_pins() if str(p.get_pin_name()) == 'Priority'][0]; before = str(pin.get_pin_value()); pin.set_pin_value(str(prio)); R['nodes'][nm] = [before, str(pin.get_pin_value())]
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['bp_saved'] = bool(EAL.save_loaded_asset(bp, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_KEY_PRIORITY', R.get('bp_saved'), R.get('error', '')[-200:])
