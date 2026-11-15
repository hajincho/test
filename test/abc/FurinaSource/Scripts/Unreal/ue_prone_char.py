"""Prone stance, character side (2026-11-15). Z toggles prone (IA_FurinaProne in IMC_FurinaStance); C while prone stands up.
 - prone = CMC crouch with a smaller capsule (CrouchedHalfHeight 42 = capsule radius; crouch is 58) + BP bool FurinaProneWant; the flag component FurinaProne (tag) = Want && IsCrouching is refreshed
   every 0.05 s in the view timer chain (after FPN_FireHoldSet) and read by ABP_Furina (curve 'Prone' -> CR_FurinaSecondary lies the body down, see ue_build_cr.py)
 - entering: Want=true, CrouchedHalfHeight=42, UnCrouch, 0.06 s later FurinaProneCrouch -> Crouch (the capsule only resizes on a fresh Crouch)
 - leaving (Z or C): Want=false, CrouchedHalfHeight=58, UnCrouch
 - speed: walk and Shift speeds are both PRONE_SPEED (no sprint): K2Node_FPT_WalkSpd / RunSpd get an outer select  Want ? PRONE_SPEED : old value
 - recoil / spread multiplier: K2Node_FPF_CrouchMul gets an outer select  Want ? PRONE_MUL (0.75 = -25 %) : old value (crouch 0.9 = -10 %)
 usage: py ue_prone_char.py [prone_speed] [prone_mul]"""
import unreal, json, traceback, sys
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
SPEED = sys.argv[1] if len(sys.argv) > 1 else '40'
MUL = sys.argv[2] if len(sys.argv) > 2 else '0.75'
def main():
    R = {}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    # ---- input
    ip = '/Game/Furina/Input/IA_FurinaProne'
    ia = unreal.load_asset(ip) if E.does_asset_exist(ip) else T.create_asset('IA_FurinaProne', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('triggers', []); ia.set_editor_property('modifiers', []); ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN); E.save_loaded_asset(ia, False)
    imc = unreal.load_asset('/Game/Furina/Input/IMC_FurinaStance')
    try: has = any(str(m.get_editor_property('action').get_name()) == 'IA_FurinaProne' for m in imc.get_editor_property('mappings'))
    except Exception:
        try: has = any(str(m.get_editor_property('action').get_name()) == 'IA_FurinaProne' for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'))
        except Exception: has = False
    if not has:
        k = unreal.Key(); k.set_editor_property('key_name', 'Z'); imc.map_key(ia, k)
    E.save_loaded_asset(imc, False); R['input'] = 'ok'
    bp = unreal.load_asset(CH)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    if 'FurinaProne' not in handles():
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()['FurinaMesh'], new_class=unreal.SceneComponent, blueprint_context=bp))
        sub.rename_subobject(h, unreal.Text('FurinaProne')); R['comp'] = 'added'
    comp = lib.get_associated_object(lib.get_data(handles()['FurinaProne'])); comp.set_editor_property('auto_activate', False); comp.set_editor_property('component_tags', ['FurinaProne']); del comp
    if 'FurinaProneWant' not in [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
        R['var_added'] = unreal.BlueprintEditorLibrary.add_member_variable(bp, 'FurinaProneWant', unreal.BlueprintEditorLibrary.get_basic_type_by_name('bool'))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    def w(a, b):
        assert a.is_valid() and b.is_valid(), (a, b)
        b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
    def call(name, path):
        n = ed.add_call_function_node(path); assert n, path; n.rename(name); nodes[name] = n; return n
    cmc_get = nodes['K2Node_FPT_GetCMCT']; cmc_out = cmc_get.find_output_pin('CharacterMovement')
    if 'FPN_ProneToggle' not in nodes:
        def want_get(name):
            g = ed.add_get_member_variable_node('FurinaProneWant'); g.rename(name); nodes[name] = g; return g.find_output_pin('FurinaProneWant')
        def want_set(name, val):
            s = ed.add_set_member_variable_node('FurinaProneWant'); s.rename(name); nodes[name] = s; s.find_input_pin('FurinaProneWant').set_pin_value(val); return s
        def half_set(name, val):
            s = ed.add_set_member_variable_node('CrouchedHalfHeight', '/Script/Engine.CharacterMovementComponent'); s.rename(name); nodes[name] = s
            w(cmc_out, s.find_self_pin()); s.find_input_pin('CrouchedHalfHeight').set_pin_value(val); return s
        ev = ed.create_node_from_name('Input|EnhancedActionEvents|IA_FurinaProne', unreal.Vector2D(0, 0), []); assert ev, 'input action node'; ev.rename('FPN_ProneToggle')
        br = ed.add_branch_node(); br.rename('FPN_ProneBranch'); w(want_get('FPN_ProneWantGet0'), br.find_input_pin('Condition')); w(ev.find_output_pin('Started'), br.find_execute_pin())
        # leave prone
        s1 = want_set('FPN_ProneOffWant', 'false'); h1 = half_set('FPN_ProneOffHalf', '58.0'); u1 = call('FPN_ProneOffUnCrouch', '/Script/Engine.Character:UnCrouch')
        w(br.find_output_pin('then'), s1.find_execute_pin()); w(s1.find_then_pin(), h1.find_execute_pin()); w(h1.find_then_pin(), u1.find_execute_pin())
        # enter prone
        s2 = want_set('FPN_ProneOnWant', 'true'); h2 = half_set('FPN_ProneOnHalf', '42.0'); u2 = call('FPN_ProneOnUnCrouch', '/Script/Engine.Character:UnCrouch')
        tm = call('FPN_ProneTimer', '/Script/Engine.KismetSystemLibrary:K2_SetTimer'); tm.find_input_pin('FunctionName').set_pin_value('FurinaProneCrouch'); tm.find_input_pin('Time').set_pin_value('0.06'); tm.find_input_pin('bLooping').set_pin_value('false')
        w(br.find_output_pin('else'), s2.find_execute_pin()); w(s2.find_then_pin(), h2.find_execute_pin()); w(h2.find_then_pin(), u2.find_execute_pin()); w(u2.find_then_pin(), tm.find_execute_pin())
        ce = ed.add_custom_event_node('FurinaProneCrouch'); ce.rename('FPN_ProneCrouchEvent'); cr = call('FPN_ProneDoCrouch', '/Script/Engine.Character:Crouch'); w(ce.find_then_pin(), cr.find_execute_pin())
        R['tm_pins'] = [str(p.get_pin_name()) for p in tm.list_all_pins()]
        # C while prone: clear prone first (inserted between the input event and the crouch toggle branch)
        crb = nodes['K2Node_FPT_CrB']; cia = nodes['K2Node_FPT_CrIA']
        cs = want_set('FPN_ProneCWant', 'false'); ch_ = half_set('FPN_ProneCHalf', '58.0')
        cia.find_output_pin('Started').break_pin_links(); w(cia.find_output_pin('Started'), cs.find_execute_pin()); w(cs.find_then_pin(), ch_.find_execute_pin()); w(ch_.find_then_pin(), crb.find_execute_pin())
        R['toggle'] = 'added'
    if 'FPN_ProneFlagSet' not in nodes:
        get = ed.add_get_member_variable_node('FurinaProne'); get.rename('FPN_ProneFlagGet'); nodes['FPN_ProneFlagGet'] = get
        setn = call('FPN_ProneFlagSet', '/Script/Engine.ActorComponent:SetActive'); w(get.find_output_pin('FurinaProne'), setn.find_self_pin()); setn.find_input_pin('bReset').set_pin_value('false')
        wg = ed.add_get_member_variable_node('FurinaProneWant'); wg.rename('FPN_ProneWantGet1'); nodes['FPN_ProneWantGet1'] = wg
        ic = call('FPN_ProneIsCrouch', '/Script/Engine.NavMovementComponent:IsCrouching'); w(cmc_out, ic.find_self_pin())
        an = call('FPN_ProneAnd', '/Script/Engine.KismetMathLibrary:BooleanAND'); w(wg.find_output_pin('FurinaProneWant'), an.find_input_pin('A')); w(ic.find_result_pin(), an.find_input_pin('B')); w(an.find_result_pin(), setn.find_input_pin('bNewActive'))
        fh = nodes['FPN_FireHoldSet']; old = list(fh.find_then_pin().list_connected_pins()); fh.find_then_pin().break_pin_links(); w(fh.find_then_pin(), setn.find_execute_pin())
        for p in old: w(setn.find_then_pin(), p)
        R['flag'] = 'added'
    def outer_select(name, base_node, a_val, pick_name):
        """new SelectFloat(A=a_val, B=base.result, bPickA=Want) and every old consumer of the base result is relinked to it"""
        base = nodes[base_node]; out = base.find_result_pin(); consumers = [p for p in out.list_connected_pins()]
        sel = call(name, '/Script/Engine.KismetMathLibrary:SelectFloat'); sel.find_input_pin('A').set_pin_value(a_val)
        g = ed.add_get_member_variable_node('FurinaProneWant'); g.rename(pick_name); nodes[pick_name] = g; w(g.find_output_pin('FurinaProneWant'), sel.find_input_pin('bPickA'))
        for p in consumers: w(sel.find_result_pin(), p)
        w(out, sel.find_input_pin('B'))
        return len(consumers)
    if 'FPN_ProneWalk' not in nodes:
        R['walk_consumers'] = outer_select('FPN_ProneWalk', 'K2Node_FPT_WalkSpd', SPEED, 'FPN_ProneWantGet2')
        R['run_consumers'] = outer_select('FPN_ProneRun', 'K2Node_FPT_RunSpd', SPEED, 'FPN_ProneWantGet3')
    if 'FPN_ProneMul' not in nodes:
        R['mul_consumers'] = outer_select('FPN_ProneMul', 'K2Node_FPF_CrouchMul', MUL, 'FPN_ProneWantGet4')
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['char_status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['char_saved'] = E.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\prone_char.json', 'w'), indent=1); print('PRONE_CHAR', R.get('char_status'), R.get('error', '')[-400:])
