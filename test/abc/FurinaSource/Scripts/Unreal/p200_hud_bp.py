"""BP_FurinaHUD: 권총 장착 시 이름 P220, SEMI 표시, MPC 스칼라(Weapon, MagSize) 전달."""
import unreal, json, uuid, traceback
PL = unreal.BlueprintGraphPinLibrary; BEL = unreal.BlueprintEditorLibrary; EAL = unreal.EditorAssetLibrary
KML = '/Script/Engine.KismetMathLibrary:'
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
R = {}
hb = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); e = unreal.BlueprintGraphEditor.get_graph_editor_by_name(hb, 'EventGraph')
def node(n): return next((x for x in e.list_all_nodes() if x.get_name() == n), None)
def link(a, b):
    assert a is not None and b is not None and a.is_valid() and b.is_valid(), 'pin'
    assert PL.try_create_connection(a, b), 'link %s.%s -> %s.%s' % (a.get_owning_node().get_name(), a.get_pin_name(), b.get_owning_node().get_name(), b.get_pin_name())
def fn(path, prefix):
    n = e.add_call_function_node(path); assert n, path; n.rename('P2H_%s_%s' % (prefix, uuid.uuid4().hex[:6])); return n
def lit(v):
    n = fn('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble', 'Lit'); n.find_input_pin('Value').set_pin_value(repr(float(v))); return n.find_result_pin()
try:
    tgt = unreal.load_asset(PAWN).generated_class().get_path_name()
    cast = node('M4HUD_Cast'); result = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
    g = e.add_get_member_variable_node('FurinaPistolOn', tgt); g.rename('P2H_GetPistol_' + uuid.uuid4().hex[:6]); link(result, g.find_self_pin())
    act = fn('/Script/Engine.ActorComponent:IsActive', 'IsPistol'); link(g.find_output_pin('FurinaPistolOn'), act.find_self_pin()); pistol = act.find_result_pin()
    # 이름 글자
    nm = fn(KML + 'SelectString', 'Name'); nm.find_input_pin('A').set_pin_value('P220'); nm.find_input_pin('B').set_pin_value('M4A1'); link(pistol, nm.find_input_pin('bPickA'))
    t = node('M4HUD_DrawAmmo').find_input_pin('Text'); t.break_pin_links(); link(nm.find_result_pin(), t)
    # SEMI: 기존 FurinaSemi 판정 OR 권총
    o = fn(KML + 'BooleanOR', 'Or'); link(node('FM_HudIsSemi').find_result_pin(), o.find_input_pin('A')); link(pistol, o.find_input_pin('B'))
    pk = node('FM_HudText').find_input_pin('bPickA'); pk.break_pin_links(); link(o.find_result_pin(), pk)
    # 스칼라 전달 (SetReloadP 뒤에 삽입)
    ref = node('FHUD_SetReloadP'); old = list(ref.find_then_pin().list_connected_pins()); ref.find_then_pin().break_pin_links()
    wc = ref.find_input_pin('WorldContextObject'); wcs = wc.list_connected_pins() if wc else []
    prev = ref
    for pname, a, b in (('Weapon', 1.0, 0.0), ('MagSize', 8.0, 20.0)):
        s = fn('/Script/Engine.KismetMaterialLibrary:SetScalarParameterValue', 'Set' + pname)
        s.find_input_pin('Collection').set_pin_value('/Game/Furina/UI/MPC_FurinaHUD.MPC_FurinaHUD'); s.find_input_pin('ParameterName').set_pin_value(pname)
        if wcs: link(wcs[0], s.find_input_pin('WorldContextObject'))
        sel = fn(KML + 'SelectFloat', 'Sel' + pname); link(lit(a), sel.find_input_pin('A')); link(lit(b), sel.find_input_pin('B')); link(pistol, sel.find_input_pin('bPickA'))
        link(sel.find_result_pin(), s.find_input_pin('ParameterValue'))
        link(prev.find_then_pin(), s.find_execute_pin()); prev = s
    for p in old: link(prev.find_then_pin(), p)
    BEL.compile_blueprint(hb); R['status'] = str(hb.get_editor_property('status')); R['errors'] = [x.get_name()[:40] for x in e.list_nodes_with_errors()][:10]
    R['wc'] = len(wcs)
except Exception: R['error'] = traceback.format_exc()[-1200:]
print('P200_HUD_BP', json.dumps(R, default=str, ensure_ascii=False))
