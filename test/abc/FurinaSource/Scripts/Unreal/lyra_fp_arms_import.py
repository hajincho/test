"""헤드리스(commandlet): 1인칭 전용 팔 FBX(소총 로컬 좌표로 구운 것)를 스태틱 메시로 가져오고 SK_Furina 머티리얼을 슬롯 이름으로 연결.
 인자: <태그>   입력 FBX/FPArms/SM_FurinaFPArm<L|R>_<태그>.fbx -> /Game/Furina/FPArms/SM_FurinaFPArm<L|R>
 검증: 메시 경계 vs Data/fp_arms_bake_<태그>.json 예상 경계.  FurinaMesh 의 VisibilityBasedAnimTickOption 도 기록.  -> Data/lyra_fp_arms_import.json"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; TAG = ARGS[0] if ARGS else 'a1'
KIND = ARGS[1] if len(ARGS) > 1 else 'rifle'   # rifle | pistol
NM = 'SM_FurinaFPArm' if KIND == 'rifle' else 'SM_FurinaFPPistArm'; BKJ = 'fp_arms_bake_%s.json' if KIND == 'rifle' else 'fp_pistol_arms_bake_%s.json'
SRC = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
R = {'tag': TAG, 'meshes': {}}
R['kind'] = None
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
try:
    R['kind'] = KIND
    BK = json.load(open(SRC + '\\Data\\' + BKJ % TAG))
    skm = unreal.load_asset('/Game/Furina/SK_Furina')
    skmats = {}
    for m in skm.get_editor_property('materials'):
        skmats[str(m.get_editor_property('material_slot_name'))] = m.get_editor_property('material_interface')
    R['sk_slots'] = {k: v.get_path_name() if v else None for k, v in skmats.items()}
    tasks = []
    for side in ('L', 'R'):
        ui = unreal.FbxImportUI()
        ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False)
        ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
        ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False)
        sd = ui.get_editor_property('static_mesh_import_data')
        for k, v in (('combine_meshes', True), ('generate_lightmap_u_vs', False), ('auto_generate_collision', False), ('remove_degenerates', False),
                     ('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS), ('convert_scene', True), ('force_front_x_axis', False),
                     ('convert_scene_unit', False), ('transform_vertex_to_absolute', True), ('import_uniform_scale', 1.0), ('build_nanite', False)):
            try: sd.set_editor_property(k, v)
            except Exception as e: R.setdefault('opt_err', []).append([k, str(e)[:80]])
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', SRC + r'\FBX\FPArms\%s%s_%s.fbx' % (NM, side, TAG))
        t.set_editor_property('destination_path', '/Game/Furina/FPArms'); t.set_editor_property('destination_name', NM + side)
        t.set_editor_property('replace_existing', True); t.set_editor_property('automated', True); t.set_editor_property('save', False); t.set_editor_property('options', ui)
        tasks.append((side, t))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t for s, t in tasks])
    for side, t in tasks:
        R['meshes'][side] = {'imported': [str(x) for x in t.get_editor_property('imported_object_paths')]}
        sm = unreal.load_asset('/Game/Furina/FPArms/' + NM + side)
        e = R['meshes'][side]
        slots = []
        for i, st in enumerate(sm.get_editor_property('static_materials')):
            nm = str(st.get_editor_property('material_slot_name')); mi = skmats.get(nm)
            if mi is None:
                for k, v in skmats.items():
                    if k.lower() in nm.lower() or nm.lower() in k.lower(): mi = v; break
            if mi is not None: sm.set_material(i, mi)
            slots.append([nm, mi.get_path_name() if mi else None])
        e['slots'] = slots
        bb = sm.get_bounding_box(); e['bmin'] = [bb.min.x, bb.min.y, bb.min.z]; e['bmax'] = [bb.max.x, bb.max.y, bb.max.z]
        ex = BK['side_' + side]; e['exp_bmin'] = ex['bmin_ue']; e['exp_bmax'] = ex['bmax_ue']
        e['bbox_err'] = max(abs(a - b) for a, b in zip(e['bmin'] + e['bmax'], ex['bmin_ue'] + ex['bmax_ue']))
        e['nv'] = sm.get_num_vertices(0); e['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(sm, False))
    # FurinaMesh 틱 옵션
    bp = unreal.load_asset(PAWN); sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    hs = {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    fm = lib.get_associated_object(lib.get_data(hs['FurinaMesh']))
    R['mesh_tick_opt'] = str(fm.get_editor_property('visibility_based_anim_tick_option'))
    R['components'] = sorted(hs.keys())
    rf = lib.get_associated_object(lib.get_data(hs['FurinaRifle'])); R['rifle_cls'] = rf.get_class().get_name()
    del bp, sub, lib, fm, rf
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(SRC + r'\Data\lyra_fp_arms_import.json', 'w'), indent=1, default=str); print('LYRA_FP_ARMS_IMPORT', R.get('error', 'ok'))
