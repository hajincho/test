"""에디터(편집 전용, PIE 아님, 2026-11-22): 제3제국 병과 캐릭터 7종 -> Saved/Classes.json("done": true)
 Blender build_class_on_furina.py 결과(FBX/Classes/<key>_cm.fbx, Data/class_<key>_build.json)를 가져와 무기창 병과 버튼에 연결.
 1) 키별 /Game/Furina/Classes/<Key>/: SK_Class_<Key>(스켈레톤 SK_Furina_Skeleton), 텍스처 T_<Key>_*, 재질 MI_<Key>_MatNN(부모 M_Furina_Opaque, BaseTex)
 2) SK_Furina_Skeleton: 몸 21 + 손가락 30 뼈 이동 리타깃 = Skeleton, Hips = AnimationScaled(각 메시 기준 뼈 길이)
 3) 캐릭터 BP: 예전 LOOK_ 노드(받은 군인 모델용)를 지우고 FurinaLook<Key> 이벤트 7개 + FurinaLookFurina(보관용, 버튼 없음)
    = 메시 교체 -> 재질 덮어쓰기 비우기(시작할 때 라이라가 현재 재질로 만든 동적 인스턴스가 남지 않게) -> FurinaLook 저장.
    기본 메시 = 보병(SK_Class_Infantry), FurinaLook 기본값 'infantry'(푸리나는 에셋만 보관, 비활성).
    1인칭 머리 숨김(LOOKH_) 조건: 외형 == 'infantry' -> 외형 != 'furina'.
 4) 무기창: '기본(푸리나)' 버튼 제거, 병과 7개 버튼 모두 활성(툴팁에 캐릭터·키), 클릭 로직(LK_) 다시 만듦.
 5) 받은 군인 모델(/Game/Furina/Soldier) 삭제."""
import json, sys, time, traceback, uuid
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib, lyra_fpvm_optics; importlib.reload(lyra_fpvm_optics)
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, wire, chain
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {}
ASSETS = unreal.EditorAssetLibrary; TOOLS = unreal.AssetToolsHelpers.get_asset_tools(); BEL = unreal.BlueprintEditorLibrary; MEL = unreal.MaterialEditingLibrary
SKEL = '/Game/Furina/SK_Furina_Skeleton'; MENU = '/Game/Furina/UI/WBP_FurinaWeaponMenu'; BASE = '/Game/Furina/Classes'
# 무기창 병과 순서(Look_1..7)와 같음
CLASSES = [('officer', 'Officer', '장교', '진', 173), ('infantry', 'Infantry', '보병', '미카', 165), ('assault', 'Assault', '돌격병', '케이아', 184),
           ('antitank', 'AntiTank', '대전차병', '클레', 125), ('heavy', 'Heavy', '중화기병', '노엘', 166), ('sniper', 'Sniper', '저격수', '엠버', 163), ('armor', 'Armor', '기갑병', '유라', 171)]
TOK = '%x' % (int(time.time()) % 0xFFFFF)


def info(key): return json.loads((FS / 'Data' / f'class_{key}_build.json').read_text(encoding='utf-8'))


def import_class(key, Key):
    d = info(key); folder = f'{BASE}/{Key}'; tdir = FS / d['textures_dir']
    texs = {}
    for t in sorted({m['texture'] for m in d['materials'] if m['texture']}):
        name = f'T_{Key}_{len(texs):02d}'; path = f'{folder}/Textures/{name}'
        if True:   # 번호는 정렬 순서라 원본 목록이 바뀌면 같은 이름에 다른 파일이 올 수 있음 -> 항상 다시 가져옴
            task = unreal.AssetImportTask(); task.filename = str(tdir / t); task.destination_path = folder + '/Textures'; task.destination_name = name
            task.automated = True; task.save = True; task.replace_existing = True; TOOLS.import_asset_tasks([task])
        texs[t] = unreal.load_asset(path); assert texs[t], (key, t)
        # 푸른 옷 텍스처(유라 服.png)를 언리얼이 노멀맵으로 자동 판정해 연두색으로 보였음 -> 색 텍스처로 고정
        texs[t].set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT); texs[t].set_editor_property('srgb', True)
        assert ASSETS.save_loaded_asset(texs[t], False)
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = True; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    ui.import_materials = False; ui.import_textures = False; ui.import_animations = False; ui.create_physics_asset = False
    ui.skeleton = unreal.load_asset(SKEL); ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets', False)
    task = unreal.AssetImportTask(); task.filename = str(FS / 'FBX' / 'Classes' / f'{key}_cm.fbx'); task.destination_path = folder; task.destination_name = f'SK_Class_{Key}'
    task.automated = True; task.save = False; task.replace_existing = True; task.options = ui; TOOLS.import_asset_tasks([task])
    mesh = unreal.load_asset(f'{folder}/SK_Class_{Key}'); assert mesh, key
    assert mesh.get_editor_property('skeleton').get_path_name().startswith(SKEL)
    parent = unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque'); by_slot = {m['slot']: m for m in d['materials']}
    slots = list(mesh.materials); miss = []
    for s in slots:
        sn = str(s.material_slot_name); m = by_slot.get(sn)
        if not m: miss.append(sn); continue
        name = f'MI_{Key}_{sn}'; path = f'{folder}/Materials/{name}'
        mi = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else TOOLS.create_asset(name, folder + '/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, parent)
        if m['texture']: MEL.set_material_instance_texture_parameter_value(mi, 'BaseTex', texs[m['texture']])
        assert ASSETS.save_loaded_asset(mi, False); s.material_interface = mi
    mesh.set_editor_property('materials', slots); assert ASSETS.save_loaded_asset(mesh, False)
    b = mesh.get_bounds()
    return {'slots': len(slots), 'missing': miss, 'textures': len(texs), 'height_cm': round(b.origin.z + b.box_extent.z, 1)}


def retarget_modes():
    body = {n.replace(' ', '-') for n in info('infantry')['body_bones']}
    sk = unreal.load_asset(SKEL); sk.modify()
    names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(unreal.AnimPoseExtensions.get_reference_pose(sk))]
    tree = sk.get_editor_property('bone_tree'); M = unreal.BoneTranslationRetargetingMode; changed = []
    assert body <= set(names), body - set(names)
    for i, n in enumerate(names):
        want = M.ANIMATION_SCALED if n == 'Hips' else (M.SKELETON if n in body else None)
        if want is None: continue
        node = tree[i]
        if node.get_editor_property('translation_retargeting_mode') != want:
            node.set_editor_property('translation_retargeting_mode', want); tree[i] = node; changed.append(n)
    assert ASSETS.save_loaded_asset(sk, False)
    return changed


def discard(editor, nodes):
    for n in nodes:
        for p in n.list_all_pins(): p.break_pin_links()
        n.rename('Discarded_' + uuid.uuid4().hex)
    if nodes: editor.remove_nodes(nodes)
    return len(nodes)


def pawn():
    bp = unreal.load_asset(PAWN); g = Graph(bp, 'LOOK_'); out = {}
    old = [n for k, n in g.nodes.items() if k.startswith('LOOK_')]
    # 예전 이벤트 노드(LOOK_Ev_*)는 이름 충돌을 피하려고 함께 지움
    out['removed'] = discard(g.editor, old); g = Graph(bp, 'LOOK_')
    if 'FurinaLook' not in [str(v) for v in BEL.list_member_variable_names(bp)]:
        BEL.add_member_variable(bp, 'FurinaLook', BEL.get_basic_type_by_name('string')); g = Graph(bp, 'LOOK_')
    looks = [(Key, f'{BASE}/{Key}/SK_Class_{Key}', key) for key, Key, *_ in CLASSES] + [('Furina', '/Game/Furina/SK_Furina', 'furina')]
    made = []
    for Key, asset, look in looks:
        ev = g.editor.add_custom_event_node('FurinaLook' + Key); assert ev, Key; ev.rename('LOOK_Ev_' + Key)
        setm = g.call('Set_' + Key, ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', target=g.get('FurinaMesh'), NewMesh=unreal.load_asset(asset))
        num = g.call('Num_' + Key, ENGINE + 'PrimitiveComponent:GetNumMaterials', target=g.get('FurinaMesh'))
        last = g.call('Last_' + Key, MATH + 'Subtract_IntInt', A=num.find_result_pin(), B=1)
        loop = g.editor.add_macro_node('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForLoop'); assert loop; loop.rename('LOOK_Loop_' + Key)
        loop.find_input_pin('FirstIndex').set_pin_value('0'); wire(last.find_result_pin(), loop.find_input_pin('LastIndex'))
        clear = g.call('Clear_' + Key, ENGINE + 'PrimitiveComponent:SetMaterial', target=g.get('FurinaMesh'))
        wire(loop.find_output_pin('Index'), clear.find_input_pin('ElementIndex')); wire(loop.find_output_pin('LoopBody'), clear.find_execute_pin())
        store = g.store('Store_' + Key, 'FurinaLook', look)
        wire(ev.find_then_pin(), setm.find_execute_pin()); wire(setm.find_then_pin(), loop.find_input_pin('execute')); wire(loop.find_output_pin('Completed'), store.find_execute_pin())
        made.append('FurinaLook' + Key)
    out['events'] = made
    # 1인칭 머리 숨김: 외형 != 'furina'
    gh = Graph(bp, 'LOOKH_')
    if 'LOOKH_NotFurina' not in gh.nodes:
        isinf = gh.nodes['LOOKH_IsInf']; isinf.find_input_pin('B').set_pin_value('furina')
        res = isinf.find_result_pin(); targets = list(res.list_connected_pins()); res.break_pin_links()
        nf = gh.call('NotFurina', MATH + 'Not_PreBool', A=res)
        for t in targets: wire(nf.find_result_pin(), t)
    BEL.compile_blueprint(bp); st = bp.get_editor_property('status'); assert st != unreal.BlueprintStatus.BS_ERROR, str(st)
    # 기본 외형 = 보병
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = next(lib.get_object(lib.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp) if str(lib.get_variable_name(lib.get_data(h))) == 'FurinaMesh')
    comp.set_editor_property('skeletal_mesh_asset', unreal.load_asset(f'{BASE}/Infantry/SK_Class_Infantry'))
    BEL.compile_blueprint(bp)
    unreal.get_default_object(unreal.SystemLibrary).call_method('SetStringPropertyByName', (unreal.get_default_object(bp.generated_class()), 'FurinaLook', 'infantry'))
    assert ASSETS.save_loaded_asset(bp, False)
    out['status'] = str(bp.get_editor_property('status')); out['default_mesh'] = comp.get_editor_property('skeletal_mesh_asset').get_name()
    return out


def menu():
    wbp = unreal.load_asset(MENU); wt = unreal.find_object(None, MENU + '.WBP_FurinaWeaponMenu:WidgetTree')
    W = {o.get_name(): o for o in unreal.ObjectIterator(unreal.Widget) if o.get_outer() == wt and not o.get_name().startswith(('Old', 'Discarded'))}
    if 'LookBox_0' in W: W['LookRow'].remove_child(W['LookBox_0']); W['LookBox_0'].rename('Discarded_' + uuid.uuid4().hex)
    for i, (key, Key, cls, who, h) in enumerate(CLASSES, 1):
        b = W['Look_%d' % i]; b.set_is_enabled(True); b.set_tool_tip_text(unreal.Text(f'외형: {cls} - {who} ({h}cm)'))
    W['LookCurrent'].set_text(unreal.Text('현재 외형: 보병')); W['LookHead'].set_text(unreal.Text('병과 (외형)  -  제3제국'))
    BEL.compile_blueprint(wbp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(wbp, 'OnPreviewMouseButtonDown'); N = {n.get_name(): n for n in ed.list_all_nodes()}
    CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
    def link(a, b): assert a and b and CONN(a, b), ('link', a.get_owning_node().get_name() if a else None, b.get_owning_node().get_name() if b else None)
    entry = [n for n in N.values() if n.get_class().get_name() == 'K2Node_FunctionEntry'][0]
    lk = [n for k, n in N.items() if k.startswith('LK_')]
    # 예전 클릭 체인의 마지막 else 가 가리키던 원래 무기 버튼 체인
    branches = sorted([n for k, n in N.items() if k.startswith('LK_B_')], key=lambda n: n.get_name())
    cont = []
    for b in branches:
        for p in b.find_else_pin().list_connected_pins():
            if not p.get_owning_node().get_name().startswith('LK_'): cont.append(p)
    if not branches: cont = list(entry.find_then_pin().list_connected_pins())
    assert cont, 'continuation'
    results = set()
    for n in lk:
        for p in n.list_all_pins():
            for q in p.list_connected_pins():
                if q.get_owning_node().get_class().get_name() == 'K2Node_FunctionResult': results.add(q.get_owning_node())
    removed = discard(ed, lk + list(results)); entry.find_then_pin().break_pin_links()
    pawn_cls = unreal.load_asset(PAWN).generated_class().get_path_name(); prev = entry.find_then_pin()
    for i, (key, Key, cls, who, h) in enumerate(CLASSES, 1):
        bn = 'Look_%d' % i
        g_ = ed.add_get_member_variable_node(bn); assert g_, bn; g_.rename('LK_G_%d_%s' % (i, TOK))
        hv = ed.add_call_function_node('/Script/UMG.Widget:IsHovered'); hv.rename('LK_H_%d_%s' % (i, TOK)); link(g_.find_output_pin(bn), hv.find_self_pin())
        br = ed.add_branch_node(); br.rename('LK_B_%d_%s' % (i, TOK)); link(hv.find_output_pin('ReturnValue'), br.find_input_pin('Condition')); link(prev, br.find_execute_pin())
        op = ed.add_call_function_node('/Script/UMG.UserWidget:GetOwningPlayerPawn'); op.rename('LK_P_%d_%s' % (i, TOK))
        cast = ed.create_node_from_name('Utilities|Casting|CastToThirdPersonCharacter_BP', unreal.Vector2D(600, 300 * i), []); assert cast; cast.rename('LK_C_%d_%s' % (i, TOK))
        link(op.find_output_pin('ReturnValue'), cast.find_input_pin('Object'))
        as_pin = next(p for p in cast.list_output_pins() if str(p.get_pin_name()).startswith('As'))
        call = ed.add_call_function_node(pawn_cls + ':FurinaLook' + Key); assert call, Key; call.rename('LK_E_%d_%s' % (i, TOK)); link(as_pin, call.find_self_pin())
        gc_ = ed.add_get_member_variable_node('LookCurrent'); gc_.rename('LK_T_%d_%s' % (i, TOK))
        st = ed.add_call_function_node('/Script/UMG.TextBlock:SetText'); st.rename('LK_S_%d_%s' % (i, TOK)); link(gc_.find_output_pin('LookCurrent'), st.find_self_pin())
        st.find_input_pin('InText').set_pin_value(f'현재 외형: {cls} ({who}, {h}cm)')
        for tag, src in (('U', st.find_then_pin()), ('UF', next(p for p in cast.list_output_pins() if str(p.get_pin_name()) == 'CastFailed'))):
            r = ed.add_return_node(); u = ed.add_call_function_node('/Script/UMG.WidgetBlueprintLibrary:Unhandled'); u.rename('LK_%s_%d_%s' % (tag, i, TOK))
            link(u.find_output_pin('ReturnValue'), r.find_input_pin('ReturnValue')); link(src, r.find_execute_pin())
        link(br.find_then_pin(), cast.find_execute_pin()); link(cast.find_then_pin(), call.find_execute_pin()); link(call.find_then_pin(), st.find_execute_pin())
        prev = br.find_else_pin()
    for p in cont: link(prev, p)
    del ed, N
    BEL.compile_blueprint(wbp); s = wbp.get_editor_property('status'); assert s != unreal.BlueprintStatus.BS_ERROR, str(s)
    assert ASSETS.save_loaded_asset(wbp, False)
    return {'removed': removed, 'status': str(s), 'continue_to': [p.get_owning_node().get_name() for p in cont]}


def delete_soldier():
    out = {}
    if ASSETS.does_directory_exist('/Game/Furina/Soldier'):
        ar = unreal.AssetRegistryHelpers.get_asset_registry(); o = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
        refs = set()
        for a in ar.get_assets_by_path('/Game/Furina/Soldier', True):
            refs |= {str(x) for x in ar.get_referencers(str(a.package_name), o) if not str(x).startswith('/Game/Furina/Soldier')}
        out['outside_refs'] = sorted(refs)
        assert not refs, refs
        out['deleted'] = ASSETS.delete_directory('/Game/Furina/Soldier')
    return out


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE first'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'; flag = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    only = [a for a in sys.argv[1:] if not a.endswith('.py')]
    want = lambda s: not only or only[0] == 'all' or s in only[0].split('+')
    try:
        if want('import'): R['import'] = {key: import_class(key, Key) for key, Key, *_ in CLASSES}
        if want('retarget'): R['retarget'] = retarget_modes()
        if want('pawn'): R['pawn'] = pawn()
        if want('menu'): R['menu'] = menu()
        if want('delete'): R['delete'] = delete_soldier()
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if flag else ' 0'))


if __name__ == '__main__':
  try: main()
  except Exception: R['error'] = traceback.format_exc()[-1800:]
  R['done'] = True; (ROOT / 'Saved' / 'Classes.json').write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False), encoding='utf-8')
  print('CLASSES', json.dumps(R, default=str, ensure_ascii=False)[:3000])
