"""Real magazine handling for the reload (2026-11-15). The magazine is its own mesh now (SM_M4Mag, split from the AR15 by Scripts/Blender/split_m4_mag.py).
Components on ThirdPersonCharacter_BP:
  FurinaMag         SM_M4Mag, child of FurinaRifle at identity (= seated in the magwell); the rifle mesh itself has no magazine any more
  FurinaMagHandRef  scene component on FurinaMesh: remembers where the magazine sits relative to the left wrist when it is gripped
Curve MagState on AS_Furina_FP_Reload / AM_Furina_FP_Reload (CR_FurinaSecondary passes it through):
  0 seated | 1 in the left hand | 2 gone (dropped / not yet fetched)
  0.00-0.40 seated, 0.40 grip -> 1 (pulled out with the hand), 0.60 released -> 2 (a physics copy BP_M4MagDrop falls to the ground),
  1.00 the hand has a fresh magazine from the belt -> 1, 1.90 pushed into the well -> 0.
  Times follow the template reload (grab f12, release f18, fresh f30, seated f57 at 30 fps).
Event FurinaMagUpdate (timer 0.016 s, started in BeginPlay) reads the curve from FurinaMesh's anim instance, rounds it to the state and
attaches / hides / spawns on every change. On grip (0 -> 1) FurinaMagHandRef is snapped to the rifle and re-attached to Left-wrist with KeepWorld,
so the relative offset is exactly the seated pose whatever the stance (first / third person differ by the TP left-hand slide).
usage: py ue_reload_mag.py"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
KEYS = [(0.0, 0), (0.37, 0), (0.43, 1), (0.57, 1), (0.63, 2), (0.97, 2), (1.03, 1), (1.87, 1), (1.93, 0), (3.1, 0)]
def main():
    R = {'log': []}
    E = unreal.EditorAssetLibrary; T = unreal.AssetToolsHelpers.get_asset_tools()
    # ---- curves
    for name in ('AS_Furina_FP_Reload', 'AM_Furina_FP_Reload'):
        a = unreal.load_asset('/Game/Furina/FP/Anim/' + name)
        if 'MagState' in [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]: unreal.AnimationLibrary.remove_curve(a, 'MagState', False)
        unreal.AnimationLibrary.add_curve(a, 'MagState', unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        unreal.AnimationLibrary.add_float_curve_keys(a, 'MagState', [k[0] for k in KEYS], [float(k[1]) for k in KEYS])
        R[name] = E.save_loaded_asset(a, False); del a
    # ---- dropped magazine actor
    p = '/Game/Furina/M4/BP_M4MagDrop'
    if not E.does_asset_exist(p):
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); T.create_asset('BP_M4MagDrop', '/Game/Furina/M4', unreal.Blueprint, f)
    dbp = unreal.load_asset(p)
    S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(bp): return {str(L.get_variable_name(L.get_data(h))): h for h in S.k2_gather_subobject_data_for_blueprint(bp)}
    def part(bp, name, cls, parent):
        hs = handles(bp)
        if name not in hs:
            h, err = S.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[parent], new_class=cls, blueprint_context=bp)); assert not str(err), str(err)
            S.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
        return L.get_associated_object(L.get_data(handles(bp)[name]))
    body = part(dbp, 'MagBody', unreal.StaticMeshComponent, 'DefaultSceneRoot')
    body.set_static_mesh(unreal.load_asset('/Game/Furina/M4/SM_M4Mag')); body.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    body.set_collision_profile_name('PhysicsActor')
    body.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_IGNORE)
    body.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_IGNORE)
    body.set_simulate_physics(True); del body
    unreal.BlueprintEditorLibrary.compile_blueprint(dbp)
    unreal.get_default_object(dbp.generated_class()).set_editor_property('initial_life_span', 8.0)
    R['drop_status'] = str(dbp.get_editor_property('status')); E.save_loaded_asset(dbp, False); del dbp
    # ---- character components
    bp = unreal.load_asset(CH)
    mag = part(bp, 'FurinaMag', unreal.StaticMeshComponent, 'FurinaRifle')
    mag.set_static_mesh(unreal.load_asset('/Game/Furina/M4/SM_M4Mag')); mag.set_collision_profile_name('NoCollision'); mag.set_editor_property('cast_shadow', True)
    mag.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); mag.set_editor_property('relative_rotation', unreal.Rotator(0, 0, 0)); mag.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1)); del mag
    ref = part(bp, 'FurinaMagHandRef', unreal.SceneComponent, 'FurinaMesh'); del ref
    ed0 = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    for v in ('FurinaMagLast',):
        if v not in [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]:
            assert ed0.add_member_variable(v, unreal.BlueprintEditorLibrary.get_basic_type_by_name('int'), '0'); R['log'].append('var ' + v)
    del ed0
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    # (ed.remove_nodes crashed the editor once - a failed partial run is simply not saved; restart the editor instead of cleaning up)
    if 'FMG_Update' not in nodes:
        def fn(name, path):
            n = ed.add_call_function_node(path); assert n, path; n.rename('FMG_' + name); return n
        def w(a, b):
            assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link failed'
        def comp(name):
            n = ed.add_get_member_variable_node(name); return n.find_output_pin(name)
        ML = '/Script/Engine.KismetMathLibrary:'; SC = '/Script/Engine.SceneComponent:'
        ev = ed.add_custom_event_node('FurinaMagUpdate'); ev.rename('FMG_Update')
        mesh, rifle, mag_c, ref_c = comp('FurinaMesh'), comp('FurinaRifle'), comp('FurinaMag'), comp('FurinaMagHandRef')
        anim = fn('Anim', '/Script/Engine.SkeletalMeshComponent:GetAnimInstance'); w(mesh, anim.find_self_pin())
        cur = fn('Curve', '/Script/Engine.AnimInstance:GetCurveValue'); w(anim.find_result_pin(), cur.find_self_pin()); cur.find_input_pin('CurveName').set_pin_value('MagState')
        rnd = fn('Round', ML + 'Round'); w(cur.find_result_pin(), rnd.find_input_pin('A'))
        last = ed.add_get_member_variable_node('FurinaMagLast'); lastp = last.find_output_pin('FurinaMagLast')
        ne = fn('Changed', ML + 'NotEqual_IntInt'); w(rnd.find_result_pin(), ne.find_input_pin('A')); w(lastp, ne.find_input_pin('B'))
        def branch(name, cond):
            n = ed.add_branch_node(); n.rename('FMG_' + name); w(cond, n.find_input_pin('Condition')); return n
        def eq(name, v):
            n = fn(name, ML + 'EqualEqual_IntInt'); w(rnd.find_result_pin(), n.find_input_pin('A')); n.find_input_pin('B').set_pin_value(str(v)); return n.find_result_pin()
        ATT = SC + 'K2_AttachToComponent'
        def attach(name, child, parent, socket, rule):
            n = fn(name, ATT); w(child, n.find_self_pin()); w(parent, n.find_input_pin('Parent'))
            n.find_input_pin('SocketName').set_pin_value(socket)
            for r in ('LocationRule', 'RotationRule', 'ScaleRule'): n.find_input_pin(r).set_pin_value(rule)
            n.find_input_pin('bWeldSimulatedBodies').set_pin_value('false'); return n
        def vis(name, comp_pin, on):
            n = fn(name, SC + 'SetVisibility'); w(comp_pin, n.find_self_pin()); n.find_input_pin('bNewVisibility').set_pin_value('true' if on else 'false'); n.find_input_pin('bPropagateToChildren').set_pin_value('false'); return n
        def chain(*ns):
            for a, b in zip(ns, ns[1:]): w(a.find_then_pin(), b.find_execute_pin())
        setl = ed.add_set_member_variable_node('FurinaMagLast'); setl.rename('FMG_SetLast'); w(rnd.find_result_pin(), setl.find_input_pin('FurinaMagLast'))
        b0 = branch('BrChanged', ne.find_result_pin()); w(ev.find_then_pin(), b0.find_execute_pin())
        b1 = branch('BrHand', eq('IsHand', 1)); w(b0.find_then_pin(), b1.find_execute_pin())
        # state 1: grip (from seated: capture the hand offset) or fresh magazine (attach to the stored offset)
        lz = fn('LastIsZero', ML + 'EqualEqual_IntInt'); w(lastp, lz.find_input_pin('A')); lz.find_input_pin('B').set_pin_value('0')
        b1a = branch('BrFromSeated', lz.find_result_pin()); w(b1.find_then_pin(), b1a.find_execute_pin())
        capA = attach('RefToRifle', ref_c, rifle, 'None', 'SnapToTarget')
        capB = attach('RefToWrist', ref_c, mesh, 'Left-wrist', 'KeepWorld')
        magH = attach('MagToRef', mag_c, ref_c, 'None', 'SnapToTarget'); visH = vis('ShowHand', mag_c, True)
        w(b1a.find_then_pin(), capA.find_execute_pin()); chain(capA, capB, magH, visH)
        magH2 = attach('MagToRef2', mag_c, ref_c, 'None', 'SnapToTarget'); visH2 = vis('ShowHand2', mag_c, True)
        w(b1a.find_output_pin('else'), magH2.find_execute_pin()); chain(magH2, visH2)
        # state 2: hide + physics copy
        b2 = branch('BrGone', eq('IsGone', 2)); w(b1.find_output_pin('else'), b2.find_execute_pin())
        xf = fn('MagWorld', SC + 'K2_GetComponentToWorld'); w(mag_c, xf.find_self_pin())
        beg = fn('DropSpawn', '/Script/Engine.GameplayStatics:BeginDeferredActorSpawnFromClass')
        beg.find_input_pin('ActorClass').set_pin_value('/Game/Furina/M4/BP_M4MagDrop.BP_M4MagDrop_C'); w(xf.find_result_pin(), beg.find_input_pin('SpawnTransform')); beg.find_input_pin('CollisionHandlingOverride').set_pin_value('AlwaysSpawn')
        fin = fn('DropFinish', '/Script/Engine.GameplayStatics:FinishSpawningActor'); w(beg.find_result_pin(), fin.find_input_pin('Actor')); w(xf.find_result_pin(), fin.find_input_pin('SpawnTransform'))
        hide = vis('HideMag', mag_c, False)
        w(b2.find_then_pin(), beg.find_execute_pin()); chain(beg, fin, hide)
        # state 0: seated again
        seat = attach('MagToRifle', mag_c, rifle, 'None', 'SnapToTarget'); visS = vis('ShowSeated', mag_c, True)
        w(b2.find_output_pin('else'), seat.find_execute_pin()); chain(seat, visS)
        for tail in (visH, visH2, hide, visS): w(tail.find_then_pin(), setl.find_execute_pin())
        # BeginPlay: start the 16 ms timer
        bp_begin = ed.find_event_node('ReceiveBeginPlay')
        timer = fn('Timer', '/Script/Engine.KismetSystemLibrary:K2_SetTimerDelegate'); w(ev.find_output_pin('OutputDelegate'), timer.find_input_pin('Delegate'))
        timer.find_input_pin('Time').set_pin_value('0.016'); timer.find_input_pin('bLooping').set_pin_value('true')
        old = list(bp_begin.find_then_pin().list_connected_pins()); bp_begin.find_then_pin().break_pin_links()
        w(bp_begin.find_then_pin(), timer.find_execute_pin())
        for q in old: w(timer.find_then_pin(), q)
        R['log'].append('graph built')
    del ed, nodes
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status'))
    if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR: R['saved'] = E.save_loaded_asset(bp, False)
    del bp
    return R
try: R = main()
except Exception: R = {'error': traceback.format_exc()}
json.dump(R, open(D + r'\reload_mag.json', 'w'), indent=1); print('RELOAD_MAG', R.get('error', 'ok')[:300])
