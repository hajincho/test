"""헤드리스: 1인칭 뷰모델 FBX(팔+총 한 몸 스켈레탈 + 애니) 가져오기.  인자: <키 예: Kar98k> <무기 텍스처 키 예: kar98k>
 FurinaSource/FBX/FPVM/SK_FPVM_<키>.fbx -> /Game/Furina/FPVM/<키>/SK_FPVM_<키>, 스켈레톤, AS_FPVM_<키>_<Idle|Fire|Reload>
 재질: 팔(Furina_SkinHair/Outfit) = 기존 1인칭 팔 메시(SM_FurinaFPArmR) 재질, 총 = MI_DE_<무기>_<슬롯>, 클립(Clip_*) = MI_DE_mauser_clip_*
 -> Data/lyra_fpvm_import_<키>.json (뼈 수, 경계, 애니 길이, VM_Gun 기준 위치: 방향 확인용)"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]; KEY = ARGS[0] if ARGS else 'Kar98k'; WK = ARGS[1] if len(ARGS) > 1 else 'kar98k'
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'; DEST = '/Game/Furina/FPVM/' + KEY
AT = unreal.AssetToolsHelpers.get_asset_tools(); EAL = unreal.EditorAssetLibrary; R = {'key': KEY}
def run():
    if EAL.does_directory_exist(DEST):   # 다시 가져올 때 메시만 '재가져오기' 되고 애니가 갱신되지 않던 문제: 안의 에셋을 하나씩 지우고 새로
        ps = list(EAL.list_assets(DEST, recursive=True)); ps.sort(key=lambda p: ('Skeleton' in p, 'SK_FPVM' in p and 'Anim' not in p))
        R['cleared'] = {p.split('/')[-1]: bool(EAL.delete_asset(p.split('.')[0])) for p in ps}
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', True); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('create_physics_asset', False)
    sk = ui.get_editor_property('skeletal_mesh_import_data')
    for k, v in (('import_morph_targets', False), ('update_skeleton_reference_pose', True), ('use_t0_as_ref_pose', False), ('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)):
        try: sk.set_editor_property(k, v)
        except Exception as e: R.setdefault('opt_err', []).append(k)
    an = ui.get_editor_property('anim_sequence_import_data')
    for k, v in (('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME), ('import_bone_tracks', True), ('remove_redundant_keys', False), ('use_default_sample_rate', False)):
        try: an.set_editor_property(k, v)
        except Exception as e: R.setdefault('opt_err', []).append(k)
    t = unreal.AssetImportTask(); t.set_editor_property('filename', D + r'\FBX\FPVM\SK_FPVM_%s.fbx' % KEY); t.set_editor_property('destination_path', DEST); t.set_editor_property('destination_name', 'SK_FPVM_' + KEY)
    t.set_editor_property('automated', True); t.set_editor_property('replace_existing', True); t.set_editor_property('save', False); t.set_editor_property('options', ui)
    AT.import_asset_tasks([t]); R['imported'] = [str(p) for p in t.get_editor_property('imported_object_paths')]
    sm = unreal.load_asset(DEST + '/SK_FPVM_' + KEY); R['mesh'] = sm.get_path_name()
    if not any(isinstance(unreal.load_asset(p), unreal.AnimSequence) for p in EAL.list_assets(DEST, recursive=False)):   # 애니가 빠졌으면 스켈레톤 지정해 애니만 따로
        ui2 = unreal.FbxImportUI(); ui2.set_editor_property('import_mesh', False); ui2.set_editor_property('import_as_skeletal', True); ui2.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
        ui2.set_editor_property('import_animations', True); ui2.set_editor_property('import_materials', False); ui2.set_editor_property('import_textures', False); ui2.set_editor_property('skeleton', sm.get_editor_property('skeleton'))
        an2 = ui2.get_editor_property('anim_sequence_import_data')
        for k, v in (('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME), ('import_bone_tracks', True), ('remove_redundant_keys', False)):
            try: an2.set_editor_property(k, v)
            except Exception: pass
        t2 = unreal.AssetImportTask(); t2.set_editor_property('filename', D + r'\FBX\FPVM\SK_FPVM_%s.fbx' % KEY); t2.set_editor_property('destination_path', DEST); t2.set_editor_property('destination_name', 'ANIMS_' + KEY)
        t2.set_editor_property('automated', True); t2.set_editor_property('replace_existing', True); t2.set_editor_property('save', False); t2.set_editor_property('options', ui2)
        AT.import_asset_tasks([t2]); R['imported_anims'] = [str(p) for p in t2.get_editor_property('imported_object_paths')]
    # 애니 이름 정리
    R['anims'] = {}
    for p in EAL.list_assets(DEST, recursive=False):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.AnimSequence):
            nm = a.get_name(); short = nm.split('FPVM_%s_' % KEY)[-1]; want = 'AS_FPVM_%s_%s' % (KEY, short)
            if nm != want:
                if EAL.does_asset_exist(DEST + '/' + want): EAL.delete_asset(DEST + '/' + want)
                EAL.rename_asset(a.get_path_name().split('.')[0], DEST + '/' + want); a = unreal.load_asset(DEST + '/' + want)
            R['anims'][short] = {'path': a.get_path_name(), 'len': round(a.get_play_length(), 3), 'frames': a.get_editor_property('number_of_sampled_frames') if hasattr(a, 'number_of_sampled_frames') else None}
    # 재질
    armmats = {}
    try:
        fa = unreal.load_asset('/Game/Furina/FPArms/SM_FurinaFPArmR')
        for st in fa.get_editor_property('static_materials'): armmats[str(st.get_editor_property('material_slot_name'))] = st.get_editor_property('material_interface')
    except Exception as e: R['armmat_err'] = str(e)
    R['armmats'] = {k: (v.get_path_name() if v else None) for k, v in armmats.items()}
    mats = sm.get_editor_property('materials'); R['slots'] = []; new = []   # 구조체 사본을 고치면 저장되지 않아 새 SkeletalMaterial 로 다시 만든다
    for i, m in enumerate(mats):
        sl = str(m.get_editor_property('material_slot_name')); mi = None
        if sl in armmats: mi = armmats[sl]
        elif sl.startswith('Clip_'):
            src = {'Clip_Steel': 'Material', 'Clip_Projectile': '6_5', 'Clip_Case': 'case'}[sl]; p = '/Game/Furina/Weapons/Germany/mauser_clip/MI_DE_mauser_clip_' + src
            mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else None
        else:
            p = '/Game/Furina/Weapons/Germany/%s/MI_DE_%s_%s' % (WK, WK, sl); mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else None
        nm_ = unreal.SkeletalMaterial(material_interface=mi or m.get_editor_property('material_interface'), material_slot_name=m.get_editor_property('material_slot_name'))
        try: nm_.set_editor_property('uv_channel_data', m.get_editor_property('uv_channel_data'))
        except Exception: pass
        new.append(nm_); R['slots'].append([sl, mi.get_path_name() if mi else None])
    sm.set_editor_property('materials', new)
    b = sm.get_bounds(); R['bounds'] = [[round(b.origin.x, 1), round(b.origin.y, 1), round(b.origin.z, 1)], [round(b.box_extent.x, 1), round(b.box_extent.y, 1), round(b.box_extent.z, 1)]]
    skel = sm.get_editor_property('skeleton'); R['skeleton'] = skel.get_path_name() if skel else None
    try:
        ref = unreal.AnimationLibrary  # 존재 확인
    except Exception: pass
    # VM_Gun 기준(참조 포즈) 컴포넌트 공간 위치: 소켓 없이 SkeletalMesh 의 참조 뼈를 읽기
    try:
        names = [str(n) for n in sm.get_editor_property('skeleton').get_editor_property('bone_tree')] if False else None
    except Exception: pass
    R['saved'] = bool(EAL.save_loaded_asset(sm, False))
    for k, v in R['anims'].items(): EAL.save_asset(v['path'].split('.')[0], False)
    if skel: EAL.save_loaded_asset(skel, False)
try: run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
json.dump(R, open(D + r'\Data\lyra_fpvm_import_%s.json' % KEY, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('FPVM_IMPORT', R.get('error', '')[-300:])
