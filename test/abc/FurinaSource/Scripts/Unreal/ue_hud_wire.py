"""Wires BP_FurinaHUD to the self-made HUD (2026-11-15): every ReceiveDrawHUD frame  Cast ok -> SetScalarParameterValue(MPC_FurinaHUD: Ammo, Reserve, Reloading) -> DrawMaterial(M_FurinaHUD, bottom right) ->
DrawText 'M4A1' (weapon name only - the ammo type text of the old supplied image is gone) -> crosshair branch. The counters are drawn by the material, the old DrawText ammo string is not used any more."""
import unreal, json, os, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {}
    E = unreal.EditorAssetLibrary
    b = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); e = unreal.BlueprintGraphEditor.get_graph_editor_by_name(b, 'EventGraph')
    target = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP').generated_class()
    nodes = {n.get_name(): n for n in e.list_all_nodes()}
    def w(a, c):
        assert a.is_valid() and c.is_valid(), (a, c)
        c.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, c), 'link failed'
    def fn(name, path):
        n = nodes.get(name)
        if not n: n = e.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n
        return n
    cast = nodes['M4HUD_Cast']; frame = nodes['TFPHUD_Frame']; text = nodes['M4HUD_DrawAmmo']; isads = nodes['K2Node_FPAH_IsAds']
    assert frame.find_input_pin('Material').set_pin_value('/Game/Furina/UI/M_FurinaHUD.M_FurinaHUD')
    result = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
    if 'FHUD_ReloadGet' not in nodes:
        g = e.add_get_member_variable_node('FurinaReloading', target.get_path_name()); g.rename('FHUD_ReloadGet'); nodes['FHUD_ReloadGet'] = g
    g = nodes['FHUD_ReloadGet']; w(result, g.find_self_pin())
    ammo_f = fn('FHUD_AmmoF', '/Script/Engine.KismetMathLibrary:Conv_IntToDouble'); w(nodes['M4HUD_Ammo'].find_output_pin('FurinaAmmo'), ammo_f.find_input_pin('InInt'))
    res_f = fn('FHUD_ReserveF', '/Script/Engine.KismetMathLibrary:Conv_IntToDouble'); w(nodes['TFPHUD_Reserve'].find_output_pin('FurinaReserve'), res_f.find_input_pin('InInt'))
    rel_f = fn('FHUD_ReloadF', '/Script/Engine.KismetMathLibrary:Conv_BoolToDouble'); w(g.find_output_pin('FurinaReloading'), rel_f.find_input_pin('InBool'))
    sets = []
    for name, par, val in (('FHUD_SetAmmo', 'Ammo', ammo_f), ('FHUD_SetReserve', 'Reserve', res_f), ('FHUD_SetReload', 'Reloading', rel_f)):
        s = fn(name, '/Script/Engine.KismetMaterialLibrary:SetScalarParameterValue')
        assert s.find_input_pin('Collection').set_pin_value('/Game/Furina/UI/MPC_FurinaHUD.MPC_FurinaHUD'); s.find_input_pin('ParameterName').set_pin_value(par)
        w(val.find_result_pin(), s.find_input_pin('ParameterValue')); sets.append(s)
    R['set_pins'] = [str(p.get_pin_name()) for p in sets[0].list_all_pins()]
    # reload progress 0..1 = FClamp(elapsed time of the character's FurinaFinishReload timer / 3.0 s reload time); the timer elapsed value is -1 when no timer runs (clamped to 0)
    tel = fn('FHUD_ReloadElapsed', '/Script/Engine.KismetSystemLibrary:K2_GetTimerElapsedTime'); w(result, tel.find_input_pin('Object')); tel.find_input_pin('FunctionName').set_pin_value('FurinaFinishReload')
    dv = fn('FHUD_ReloadDiv', '/Script/Engine.KismetMathLibrary:Divide_DoubleDouble'); w(tel.find_result_pin(), dv.find_input_pin('A')); dv.find_input_pin('B').set_pin_value('3.0')
    cl = fn('FHUD_ReloadClamp', '/Script/Engine.KismetMathLibrary:FClamp'); w(dv.find_result_pin(), cl.find_input_pin('Value')); cl.find_input_pin('Min').set_pin_value('0.0'); cl.find_input_pin('Max').set_pin_value('1.0')
    sp = fn('FHUD_SetReloadP', '/Script/Engine.KismetMaterialLibrary:SetScalarParameterValue')
    assert sp.find_input_pin('Collection').set_pin_value('/Game/Furina/UI/MPC_FurinaHUD.MPC_FurinaHUD'); sp.find_input_pin('ParameterName').set_pin_value('ReloadP'); w(cl.find_result_pin(), sp.find_input_pin('ParameterValue'))
    # exec: Cast.then -> SetAmmo -> SetReserve -> SetReload -> SetReloadP -> Frame -> Text -> IsAds
    w(cast.find_then_pin(), sets[0].find_execute_pin()); w(sets[0].find_then_pin(), sets[1].find_execute_pin()); w(sets[1].find_then_pin(), sets[2].find_execute_pin()); w(sets[2].find_then_pin(), sp.find_execute_pin()); w(sp.find_then_pin(), frame.find_execute_pin())
    # weapon name only
    text.find_input_pin('Text').break_pin_links(); assert text.find_input_pin('Text').set_pin_value('M4A1')
    text.find_input_pin('TextColor').set_pin_value('(R=0.8,G=0.96,B=1.0,A=1.0)')
    nodes['TFPHUD_NumXOffsetLiteralB'].find_input_pin('Value').set_pin_value('0.075'); nodes['TFPHUD_NumYOffsetLiteralB'].find_input_pin('Value').set_pin_value('0.085')
    del e, nodes, cast, frame, text, isads, result, g, ammo_f, res_f, rel_f, sets
    unreal.BlueprintEditorLibrary.compile_blueprint(b); R['status'] = str(b.get_editor_property('status')); R['ok'] = b.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    if R['ok']: R['saved'] = E.save_loaded_asset(b, False)
    del b
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(os.path.join(D, 'hud_wire.json'), 'w'), indent=1); print('HUD_WIRE', R.get('ok'), R.get('error', '')[-300:])
