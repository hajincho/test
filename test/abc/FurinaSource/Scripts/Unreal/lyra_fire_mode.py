"""Lyra 에디터(헤드리스, 에디터 창은 닫은 상태): 견착 카메라 낮추기 + B 키 연사/단발 전환 + HUD 에 발사 모드 표시.
 1) ThirdPersonCharacter_BP.K2Node_FPT_TgtZ 의 견착 쪽 값(A) 20 -> SHOULDER_Z (CameraBoom.SocketOffset Z 목표값, cm)
 2) 컴포넌트 플래그 FurinaSemi (활성 = 단발, 비활성 = 연사[기본]) + IA_FurinaFireMode 를 Default_IMC 의 B 키에 매핑
 3) EventGraph: IA_FurinaFireMode Started -> ToggleActive(FurinaSemi)
    IA_FurinaFireRifle Started 의 Set Timer(FurinaRifleShot): bLooping = NOT FurinaSemi.IsActive, InitialStartDelay = Select(Semi ? 0 : -0.074)
 4) BP_FurinaHUD: M4HUD_DrawAmmo 뒤에 DrawText(AUTO/SEMI) 추가
환경변수 FM_DRY=1 이면 저장하지 않는다. 결과 -> FurinaSource/Data/lyra_fire_mode.json"""
import unreal, json, os, traceback
OUT = r'L:\FurinaSource\Data\lyra_fire_mode.json'
DRY = os.environ.get('FM_DRY') == '1'
SHOULDER_Z = '0.000000'
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
R = {'dry': DRY, 'log': []}
eal = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary; PL = unreal.BlueprintGraphPinLibrary
def w(a, b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(), 'pin invalid'
    assert PL.try_create_connection(a, b), 'link failed %s -> %s' % (a.get_pin_name(), b.get_pin_name())
def step(name, fn):
    try: R['log'].append([name, fn()])
    except Exception: R['log'].append([name, 'ERROR ' + traceback.format_exc()[-900:]])
def key(n): k = unreal.Key(); k.set_editor_property('key_name', n); return k
bp = unreal.load_asset(PAWN)
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
def nodes(e): return {n.get_name(): n for n in e.list_all_nodes()}

def camera():
    n = nodes(ed)['K2Node_FPT_TgtZ']; before = str(n.find_input_pin('A').get_pin_value())
    n.find_input_pin('A').set_pin_value(SHOULDER_Z)
    return [before, str(n.find_input_pin('A').get_pin_value())]

def mapping():
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
    R['B_before'] = [m for m in listing() if m[0] == 'B']
    ia = unreal.load_asset('/Game/Furina/Input/IA_FurinaFireMode')
    if ('B', 'IA_FurinaFireMode') not in listing(): imc.map_key(ia, key('B'))
    if not DRY: eal.save_loaded_asset(imc, False)
    return [m for m in listing() if m[0] == 'B']

def component():
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    hs = handles()
    if 'FurinaSemi' not in hs:
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaSemi'))
    comp = lib.get_associated_object(lib.get_data(handles()['FurinaSemi']))
    comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', ['FurinaSemi'])
    BEL.compile_blueprint(bp)
    return 'FurinaSemi' in handles()

def graph():
    global ed
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    N = nodes(ed); tgt = bp.generated_class().get_path_name()
    def fn(name, path):
        n = nodes(ed).get(name)
        if not n:
            n = ed.add_call_function_node(path); assert n, path; n.rename(name)
        return n
    def semi_get(name):
        n = nodes(ed).get(name)
        if not n:
            n = ed.add_get_member_variable_node('FurinaSemi', tgt); assert n, 'getvar'; n.rename(name)
        return n
    # --- toggle on B
    evt = nodes(ed).get('FM_ModeIA')
    if not evt:
        evt = ed.create_node_from_name('Input|EnhancedActionEvents|IA_FurinaFireMode', unreal.Vector2D(-2400, 6200), []); assert evt, 'IA event'; evt.rename('FM_ModeIA')
    g1 = semi_get('FM_GetSemi1'); tog = fn('FM_Toggle', '/Script/Engine.ActorComponent:ToggleActive')
    if not evt.find_output_pin('Started').list_connected_pins():
        w(g1.find_output_pin('FurinaSemi'), tog.find_self_pin()); w(evt.find_output_pin('Started'), tog.find_execute_pin())
    # --- rifle auto timer
    timer = nodes(ed)['K2Node_FPF_Auto']
    g2 = semi_get('FM_GetSemi2'); act = fn('FM_IsSemi', '/Script/Engine.ActorComponent:IsActive'); w(g2.find_output_pin('FurinaSemi'), act.find_self_pin())
    nt = fn('FM_NotSemi', '/Script/Engine.KismetMathLibrary:Not_PreBool'); w(act.find_result_pin(), nt.find_input_pin('A'))
    lp = timer.find_input_pin('bLooping'); lp.break_pin_links(); w(nt.find_result_pin(), lp)
    sel = fn('FM_Delay', '/Script/Engine.KismetMathLibrary:SelectFloat'); sel.find_input_pin('A').set_pin_value('0.0'); sel.find_input_pin('B').set_pin_value('-0.074')
    w(act.find_result_pin(), sel.find_input_pin('bPickA'))
    dl = timer.find_input_pin('InitialStartDelay'); dl.break_pin_links(); w(sel.find_result_pin(), dl)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    return [str(bp.get_editor_property('status'))]

def hud():
    hb = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); e = unreal.BlueprintGraphEditor.get_graph_editor_by_name(hb, 'EventGraph')
    def node(n): return next((x for x in e.list_all_nodes() if x.get_name() == n), None)
    def fn(name, path):
        n = node(name)
        if not n:
            n = e.add_call_function_node(path); assert n, path; n.rename(name)
        return n
    if node('FM_DrawMode'): return 'already'
    ammo = node('M4HUD_DrawAmmo'); cast = node('M4HUD_Cast'); assert ammo and cast, 'hud nodes'
    result = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
    tgt = unreal.load_asset(PAWN).generated_class()
    get = e.add_get_member_variable_node('FurinaSemi', tgt.get_path_name()); get.rename('FM_HudGetSemi'); w(result, get.find_self_pin())
    act = fn('FM_HudIsSemi', '/Script/Engine.ActorComponent:IsActive'); w(get.find_output_pin('FurinaSemi'), act.find_self_pin())
    txt = fn('FM_HudText', '/Script/Engine.KismetMathLibrary:SelectString'); txt.find_input_pin('A').set_pin_value('SEMI'); txt.find_input_pin('B').set_pin_value('AUTO'); w(act.find_result_pin(), txt.find_input_pin('bPickA'))
    draw = fn('FM_DrawMode', '/Script/Engine.HUD:DrawText'); w(txt.find_result_pin(), draw.find_input_pin('Text'))
    for pin in ('TextColor', 'Font'):
        v = ammo.find_input_pin(pin); con = v.list_connected_pins()
        if con: w(con[0], draw.find_input_pin(pin))
        else: draw.find_input_pin(pin).set_pin_value(str(v.get_pin_value()))
    # 위치: 숫자 X 와 같은 X, 프레임 위쪽(Y + 높이*0.12)
    nx = node('TFPHUD_NumX'); y = node('TFPHUD_Y'); h = node('TFPHUD_Height'); sc = ammo.find_input_pin('Scale').list_connected_pins()
    w(nx.find_result_pin(), draw.find_input_pin('ScreenX'))
    off = fn('FM_HudYOff', '/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble'); w(h.find_result_pin(), off.find_input_pin('A')); off.find_input_pin('B').set_pin_value('0.12')
    yy = fn('FM_HudY', '/Script/Engine.KismetMathLibrary:Add_DoubleDouble'); w(y.find_result_pin(), yy.find_input_pin('A')); w(off.find_result_pin(), yy.find_input_pin('B')); w(yy.find_result_pin(), draw.find_input_pin('ScreenY'))
    if sc:
        ms = fn('FM_HudScale', '/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble'); w(sc[0], ms.find_input_pin('A')); ms.find_input_pin('B').set_pin_value('0.75'); w(ms.find_result_pin(), draw.find_input_pin('Scale'))
    # 실행 체인: ammo.then -> draw -> (기존 다음 노드)
    old = list(ammo.find_then_pin().list_connected_pins()); ammo.find_then_pin().break_pin_links()
    w(ammo.find_then_pin(), draw.find_execute_pin())
    for p in old: w(draw.find_then_pin(), p)
    BEL.compile_blueprint(hb); R['hud_status'] = str(hb.get_editor_property('status'))
    if not DRY and hb.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['hud_saved'] = eal.save_loaded_asset(hb, False)
    return R['hud_status']

step('camera', camera); step('mapping', mapping); step('component', component); step('graph', graph); step('hud', hud)
R['pawn_status'] = str(bp.get_editor_property('status'))
if not DRY and bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['pawn_saved'] = eal.save_loaded_asset(bp, False)
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIRE_MODE', R['pawn_status'], R.get('pawn_saved'))
