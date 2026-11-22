"""에디터(편집 전용, 2026-11-22): MG42 설치물(1단계) -> Saved/MG42Emplacement.json
 Blender mg42_assets.py export 결과(FBX/MG42, Data/mg42_emplacement.json)를 씀. 좌표: Blender cm (x, y, z) -> UE (x, -y, z), 총구 = UE +Y.
 A) 에셋: SM_MG42_Deployed(양각대 편 총) / SM_MG42_BoxOpen / SM_MG42_BoxClosed / SM_MG42_BeltUnit(탄 한 발 + 고리)
    재질: 총 = 기존 MI_DE_mg42_*, 상자 = 받은 텍스처(Box_*)로 MI_MG42_Box, 탄 = 황동 탄피·구리 뇌관·톰백 탄두·흑색 강철 고리(MI, M_FurinaWeaponPBR 의 Tint/Metal/Rough)
 B) BP_FurinaMG42(Actor): Gun, Box, Belt(InstancedStaticMesh 250개 = 늘어진 탄띠 SpanN 개 + 상자 안 자리), 변수 Rounds(250)·SpanN·Orig(자리 변환 250개)
    이벤트 ApplyRounds: 남은 탄 수만큼만 보임 - 늘어진 탄띠는 급탄구 쪽부터 남고, 상자 안은 깊은 자리부터 남음(탄띠가 위에서부터 빠져나감). BeginPlay 때 한 번.
 C) 캐릭터 이벤트 FurinaDeployMG42: 앞 1.1m 바닥으로 광선 -> 경사 20° 이하면 그 자리에 총이 캐릭터가 보는 쪽을 향하게 설치.
    무기 키가 'mg42' 로 바뀌면(무기창 MG42) 설치하고 키는 이전 무기(kar98k)로 되돌림. 들고 다니기·사격 자세·사격·재장전·탄띠 물리는 다음 단계."""
import json, math, sys, time, traceback
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, STRINGS, PAWN, Graph, chain, wire, literal
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); MEL = unreal.MaterialEditingLibrary; BEL = unreal.BlueprintEditorLibrary
DEST = '/Game/Furina/MG42'; BPPATH = DEST + '/BP_FurinaMG42'; GS = ENGINE + 'GameplayStatics:'; KSL = ENGINE + 'KismetSystemLibrary:'
EMP = json.loads((FS / 'Data' / 'mg42_emplacement.json').read_text(encoding='utf-8'))
BOXTEX = Path(r'C:\Users\fromj\AppData\Local\Temp\mg42box_src\textures')
TOK = '%x' % (int(time.time()) % 0xFFFFF)


def uv(v): return unreal.Vector(float(v[0]), -float(v[1]), float(v[2]))


def import_sm(name):
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.static_mesh_import_data.set_editor_property('combine_meshes', True); ui.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
    t = unreal.AssetImportTask(); t.filename = str(FS / 'FBX' / 'MG42' / f'{name}.fbx'); t.destination_path = DEST; t.destination_name = name
    t.automated = True; t.save = False; t.replace_existing = True; t.options = ui; TOOLS.import_asset_tasks([t]); m = unreal.load_asset(f'{DEST}/{name}'); assert m, name; return m


def mi(name, parent='/Game/Furina/Weapons/Materials/M_FurinaWeaponPBR'):
    p = f'{DEST}/Materials/{name}'
    m = unreal.load_asset(p) if ASSETS.does_asset_exist(p) else TOOLS.create_asset(name, DEST + '/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset(parent)); return m


def flat(name, rgb, metal, rough):
    m = mi(name); MEL.set_material_instance_vector_parameter_value(m, 'Tint', unreal.LinearColor(*rgb, 1.0))
    for k, v in (('MetalScale', 0.0), ('MetalAdd', metal), ('RoughScale', 0.0), ('RoughAdd', rough)): MEL.set_material_instance_scalar_parameter_value(m, k, v)
    assert ASSETS.save_loaded_asset(m, False); return m


def assets():
    out = {}
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); cv = 'Interchange.FeatureFlags.Import.FBX'
    unreal.SystemLibrary.execute_console_command(world, cv + ' 0')
    try: M = {n: import_sm(n) for n in ('SM_MG42_Deployed', 'SM_MG42_BoxOpen', 'SM_MG42_BoxClosed', 'SM_MG42_BeltUnit')}
    finally: unreal.SystemLibrary.execute_console_command(world, cv + ' 1')
    # 총: 기존 재질
    src = {str(s.material_slot_name): s.material_interface for s in unreal.load_asset('/Game/Furina/Weapons/Germany/mg42/SM_DE_mg42').static_materials}
    g = M['SM_MG42_Deployed']
    for i, s in enumerate(g.static_materials):
        if str(s.material_slot_name) in src: g.set_material(i, src[str(s.material_slot_name)])
    # 상자 텍스처
    texs = {}
    for k, (param, srgb) in {'BaseColor': ('BaseColorTex', True), 'NormalGL': ('NormalTex', False), 'Roughness': ('RoughTex', False), 'Metallic': ('MetalTex', False)}.items():
        nm = f'T_MG42_Box_{k}'; t = unreal.AssetImportTask(); t.filename = str(BOXTEX / f'Box_{k}.png'); t.destination_path = DEST + '/Textures'; t.destination_name = nm
        t.automated = True; t.save = False; t.replace_existing = True; TOOLS.import_asset_tasks([t]); tx = unreal.load_asset(f'{DEST}/Textures/{nm}'); assert tx, k
        tx.set_editor_property('srgb', srgb)
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP if k == 'NormalGL' else (unreal.TextureCompressionSettings.TC_DEFAULT if srgb else unreal.TextureCompressionSettings.TC_MASKS))
        if k == 'NormalGL': tx.set_editor_property('flip_green_channel', True)   # OpenGL 노멀 -> UE(DirectX)
        assert ASSETS.save_loaded_asset(tx, False); texs[param] = tx
    mb = mi('MI_MG42_Box')
    for p, tx in texs.items(): MEL.set_material_instance_texture_parameter_value(mb, p, tx)
    assert ASSETS.save_loaded_asset(mb, False)
    seal = flat('MI_MG42_LidSeal', (0.03, 0.03, 0.03), 0.0, 0.8)
    for box in (M['SM_MG42_BoxOpen'], M['SM_MG42_BoxClosed']):
        for i, s in enumerate(box.static_materials): box.set_material(i, seal if 'Charcoal' in str(s.material_slot_name) or 'Lid' in str(s.material_slot_name) else mb)
    U = {'MG42_Case_Brass': flat('MI_MG42_CaseBrass', (0.80, 0.60, 0.26), 1.0, 0.32), 'MG42_Primer_Copper': flat('MI_MG42_PrimerCopper', (0.72, 0.36, 0.20), 1.0, 0.35),
         'MG42_Bullet_Tombac': flat('MI_MG42_BulletTombac', (0.70, 0.42, 0.24), 1.0, 0.30), 'MG42_Link_Steel': flat('MI_MG42_LinkSteel', (0.06, 0.06, 0.065), 0.8, 0.55)}
    u = M['SM_MG42_BeltUnit']
    for i, s in enumerate(u.static_materials):
        for k, m in U.items():
            if k in str(s.material_slot_name): u.set_material(i, m)
    for m in M.values(): assert ASSETS.save_loaded_asset(m, False)
    out['slots'] = {n: [str(s.material_slot_name) for s in m.static_materials] for n, m in M.items()}
    return M, out


def xform(e):
    x = uv(e['xdir']); z = uv(e['zdir']); r = unreal.MathLibrary.make_rot_from_xz(x, z)
    return unreal.Transform(location=uv(e['loc']), rotation=r, scale=unreal.Vector(1, 1, 1))


def build_bp(M):
    out = {}
    bp = unreal.load_asset(BPPATH)
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); bp = TOOLS.create_asset('BP_FurinaMG42', DEST, unreal.Blueprint, f)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = sub.k2_gather_subobject_data_for_blueprint(bp); names = {str(lib.get_variable_name(lib.get_data(h))): h for h in hs}
    root = hs[0]
    def comp(name, cls):
        if name in names: return lib.get_object(lib.get_data(names[name]))
        p = unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp); h, fail = sub.add_new_subobject(p); assert not str(fail), fail
        sub.rename_subobject(h, unreal.Text(name)); return lib.get_object(lib.get_data(h))
    gun = comp('Gun', unreal.StaticMeshComponent); gun.set_editor_property('static_mesh', M['SM_MG42_Deployed'])
    box = comp('Box', unreal.StaticMeshComponent); box.set_editor_property('static_mesh', M['SM_MG42_BoxOpen'])
    box.set_editor_property('relative_location', uv(EMP['box_pos'])); box.set_editor_property('relative_rotation', unreal.Rotator(0, 0, -float(EMP['box_yaw_deg'])))
    belt = comp('Belt', unreal.InstancedStaticMeshComponent); belt.set_editor_property('static_mesh', M['SM_MG42_BeltUnit'])
    belt.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); belt.set_editor_property('cast_shadow', True)
    span = EMP['span']; slots = EMP['slots']; S = len(span)
    orig = [xform(e) for e in span] + [xform(e) for e in slots[S:]]
    belt.clear_instances()
    for t in orig: belt.add_instance(t)
    out['instances'] = belt.get_instance_count(); out['span_n'] = S
    have = [str(v) for v in BEL.list_member_variable_names(bp)]
    for v, t in (('Rounds', BEL.get_basic_type_by_name('int')), ('SpanN', BEL.get_basic_type_by_name('int'))):
        if v not in have: BEL.add_member_variable(bp, v, t)
    if 'Orig' not in have: BEL.add_member_variable(bp, 'Orig', BEL.get_array_type(BEL.get_struct_type(unreal.Transform.static_struct())))
    if 'HiddenXf' not in have: BEL.add_member_variable(bp, 'HiddenXf', BEL.get_struct_type(unreal.Transform.static_struct()))
    BEL.compile_blueprint(bp)
    # ApplyRounds 그래프
    g = Graph(bp, 'MGR%s_' % TOK)
    if not any(n.startswith('MGR') and ('_Update' in n) for n in g.nodes):
        ev = g.editor.add_custom_event_node('ApplyRounds'); ev.rename('MGR%s_Event' % TOK)
        loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'); loop.rename('MGR%s_Loop' % TOK)
        literal(loop, 'FirstIndex', 0); literal(loop, 'LastIndex', 249); wire(ev.find_then_pin(), loop.find_input_pin('execute'))
        i = loop.find_output_pin('Index')
        def v(n): return n.find_result_pin() if hasattr(n, 'find_result_pin') else n
        a1 = g.call('LtS', MATH + 'Less_IntInt', A=i, B=g.get('SpanN')).find_result_pin(); a2 = g.call('LtN', MATH + 'Less_IntInt', A=i, B=g.get('Rounds')).find_result_pin()
        inspan = g.call('InSpan', MATH + 'BooleanAND', A=a1, B=a2).find_result_pin()
        thr = g.call('Thr0', MATH + 'Subtract_IntInt', A=g.get('SpanN'), B=g.get('Rounds')).find_result_pin(); thr = g.call('Thr', MATH + 'Add_IntInt', A=thr, B=250).find_result_pin()
        b1 = g.call('GeS', MATH + 'GreaterEqual_IntInt', A=i, B=g.get('SpanN')).find_result_pin(); b2 = g.call('GeThr', MATH + 'GreaterEqual_IntInt', A=i, B=thr).find_result_pin()
        inbox = g.call('InBox', MATH + 'BooleanAND', A=b1, B=b2).find_result_pin(); vis = g.call('Vis', MATH + 'BooleanOR', A=inspan, B=inbox).find_result_pin()
        get = g.editor.add_call_function_node('/Script/Engine.KismetArrayLibrary:Array_Get'); get.rename('MGR%s_ArrItem' % TOK); wire(g.get('Orig'), get.find_input_pin('TargetArray')); wire(i, get.find_input_pin('Index'))
        sel = g.call('Sel', MATH + 'SelectTransform', A=get.find_output_pin('Item'), B=g.get('HiddenXf'), bPickA=vis).find_result_pin()
        last = g.call('Last', MATH + 'EqualEqual_IntInt', A=i, B=249).find_result_pin()
        up = g.call('Update', ENGINE + 'InstancedStaticMeshComponent:UpdateInstanceTransform', target=g.get('Belt'), InstanceIndex=i, NewInstanceTransform=sel, bWorldSpace=False, bMarkRenderStateDirty=last, bTeleport=True)
        wire(loop.find_output_pin('LoopBody'), up.find_execute_pin())
        bpn = g.editor.find_event_node('ReceiveBeginPlay') or g.editor.add_event_node('/Script/Engine.Actor:ReceiveBeginPlay')
        call = g.call('BeginApply', bp.generated_class().get_path_name() + ':ApplyRounds') if False else None
        cev = g.editor.add_call_function_node(BPPATH + '.BP_FurinaMG42_C:ApplyRounds');
        if cev: cev.rename('MGR%s_BeginApply' % TOK); chain(bpn.find_then_pin(), [cev])
        out['graph'] = 'built'
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); out['status'] = str(st); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('Rounds', 250); cdo.set_editor_property('SpanN', S); cdo.set_editor_property('Orig', orig)
    cdo.set_editor_property('HiddenXf', unreal.Transform(location=unreal.Vector(0, 0, 0), rotation=unreal.Rotator(0, 0, 0), scale=unreal.Vector(0, 0, 0)))
    assert ASSETS.save_loaded_asset(bp, False); return out


def pawn_graph():
    out = {}; bp = unreal.load_asset(PAWN); g = Graph(bp, 'MGD%s_' % TOK)
    if any(n.startswith('MGD') and n.endswith('_Call') for n in g.nodes): return 'exists'
    ev = g.editor.add_custom_event_node('FurinaDeployMG42'); ev.rename('MGD%s_Event' % TOK)
    def v(n, pin=None): return n.find_output_pin(pin) if pin else n.find_result_pin()
    loc = v(g.call('Loc', ENGINE + 'Actor:K2_GetActorLocation')); fwd = v(g.call('Fwd', ENGINE + 'Actor:GetActorForwardVector'))
    ahead = v(g.call('Ahead', MATH + 'Multiply_VectorFloat', A=fwd, B=110.0)); p0 = v(g.call('P0a', MATH + 'Add_VectorVector', A=loc, B=ahead))
    start = v(g.call('Start', MATH + 'Add_VectorVector', A=p0, B='0.0,0.0,60.0')); end = v(g.call('End', MATH + 'Subtract_VectorVector', A=p0, B='0.0,0.0,300.0'))
    tr = g.call('Trace', KSL + 'LineTraceSingle', Start=start, End=end, TraceChannel='TraceTypeQuery1', bTraceComplex=False, DrawDebugType='None', bIgnoreSelf=True)
    brk = g.editor.add_call_function_node('/Script/Engine.GameplayStatics:BreakHitResult'); brk.rename('MGD%s_Break' % TOK); wire(tr.find_output_pin('OutHit'), brk.find_input_pin('Hit'))
    nz = v(g.call('NZ', MATH + 'BreakVector', InVec=brk.find_output_pin('ImpactNormal')), 'Z')
    flat_ = g.call('Flat', MATH + 'GreaterEqual_DoubleDouble', A=nz, B=math.cos(math.radians(20.0))).find_output_pin('ReturnValue')   # 경사 20° 이하
    ok = g.call('Ok', MATH + 'BooleanAND', A=tr.find_output_pin('ReturnValue'), B=flat_).find_output_pin('ReturnValue'); br = g.branch('Can', ok)
    yaw = v(g.call('Yaw', MATH + 'BreakRotator', InRot=v(g.call('Rot', ENGINE + 'Actor:K2_GetActorRotation'))), 'Yaw')
    yaw2 = v(g.call('Yaw2', MATH + 'Add_DoubleDouble', A=yaw, B=-90.0))   # 총구 = 설치물 +Y -> 캐릭터가 보는 쪽(+X)
    rot = v(g.call('MkRot', MATH + 'MakeRotator', Roll=0.0, Pitch=0.0, Yaw=yaw2))
    xf = v(g.call('Xf', MATH + 'MakeTransform', Location=brk.find_output_pin('ImpactPoint'), Rotation=rot, Scale='1.0,1.0,1.0'))
    cls = BPPATH + '.BP_FurinaMG42_C'
    sp = g.call('Spawn', GS + 'BeginDeferredActorSpawnFromClass', ActorClass=cls, SpawnTransform=xf, CollisionHandlingOverride='AlwaysSpawn')
    fin = g.call('Finish', GS + 'FinishSpawningActor', Actor=v(sp), SpawnTransform=xf)
    keep = g.store('Last', 'FurinaMG42', v(fin)) if 'FurinaMG42' in [str(x) for x in BEL.list_member_variable_names(bp)] else None
    wire(ev.find_then_pin(), tr.find_execute_pin()); wire(tr.find_then_pin(), br.find_execute_pin()); chain(br.find_then_pin(), [sp, fin] + ([keep] if keep else []))
    # 무기 키가 mg42 로 바뀌면 설치 + 키를 kar98k 로(들고 다니기는 다음 단계)
    BEL.compile_blueprint(bp); g = Graph(bp, 'MGD%s_' % TOK)   # 새 이벤트를 부르려면 먼저 컴파일
    swap = g.locate('VW_S_7_').find_then_pin(); after = list(swap.list_connected_pins()); swap.break_pin_links()
    is_mg = g.branch('IsMG42', v(g.call('KeyMG42', STRINGS + 'EqualEqual_StrStr', A=g.get('FurinaPrimaryKey'), B='mg42')))
    wire(swap, is_mg.find_execute_pin())
    call = g.editor.add_call_function_node(bp.generated_class().get_path_name() + ':FurinaDeployMG42'); call.rename('MGD%s_Call' % TOK)
    back = g.store('BackKey', 'FurinaPrimaryKey', 'kar98k')
    tail = chain(is_mg.find_then_pin(), [call, back])
    for t in after: wire(tail, t); wire(is_mg.find_else_pin(), t)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); out['status'] = str(st); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    assert ASSETS.save_loaded_asset(bp, False); return out


try:
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    only = [a for a in sys.argv[1:] if not a.endswith('.py')]; want = lambda s: not only or s in only[0].split('+')
    M = None
    if want('assets') or want('bp'): M, R['assets'] = assets()
    if want('bp'): R['bp'] = build_bp(M)
    if want('pawn'): R['pawn'] = pawn_graph()
except Exception: R['error'] = traceback.format_exc()[-1800:]
R['done'] = True; (ROOT / 'Saved' / 'MG42Emplacement.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8'); print('MG42_EMP', json.dumps(R, default=str, ensure_ascii=False)[:2000])
