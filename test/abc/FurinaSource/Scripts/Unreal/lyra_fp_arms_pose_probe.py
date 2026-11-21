"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1 로 백그라운드 실행): 1인칭 소총 대기 자세의 뼈 변환 기록 (1인칭 전용 팔 굽기용).
 기록: Data/lyra_fp_arms_pose_<태그>.json
   bones: {뼈: {parent, cs:[loc,q,scale], ws:[loc,q], ref:[loc,q,scale](부모 기준 참조 포즈)}}   (cs = 메시 컴포넌트 공간)
   mesh/rifle/fpcam 월드 변환, 표본 여러 개(손목-소총 관계 안정성 확인)
 캡처: Data/fparms_<태그>_fp.png (1인칭 화면)"""
import unreal, json, sys, time, traceback, math
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_fp_arms_pose_%s.json' % TAG
R = {'tag': TAG, 'samples': []}; S = {'st': 'open', 't': 0, 'n': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def tfj(t): return {'loc': [t.translation.x, t.translation.y, t.translation.z], 'q': [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w], 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z]}
def record(p, full):
    mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); rf = comp(p, 'FurinaRifle'); cam = comp(p, 'FPCamera')
    smp = {'mesh': tfj(mesh.get_world_transform()), 'rifle': tfj(rf.get_world_transform()), 'fpcam': tfj(cam.get_world_transform()), 'fpcam_active': cam.is_active()}
    smp['rifle_parent'] = [str(rf.get_attach_parent().get_name()) if rf.get_attach_parent() else None, str(rf.get_attach_socket_name())]
    for cn in ('FurinaPistolFrame', 'FurinaPistolSlide'):
        cc = comp(p, cn, unreal.StaticMeshComponent)
        if cc is not None:
            e = tfj(cc.get_world_transform()); bb = cc.static_mesh.get_bounding_box(); e['bmin'] = [bb.min.x, bb.min.y, bb.min.z]; e['bmax'] = [bb.max.x, bb.max.y, bb.max.z]; e['rel'] = tfj(cc.get_relative_transform()) if hasattr(cc, 'get_relative_transform') else None
            smp[cn] = e
    smp['pistol_on'] = p.get_editor_property('FurinaPistolOn').is_active()
    smp['rifle_rel'] = tfj(rf.get_relative_transform()) if hasattr(rf, 'get_relative_transform') else None
    bones = {}
    n = mesh.get_num_bones()
    for i in range(n):
        bn = mesh.get_bone_name(i); s = str(bn)
        cs = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_COMPONENT); ws = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_WORLD)
        e = {'cs': tfj(cs), 'ws': tfj(ws)}
        if full:
            e['parent'] = str(mesh.get_parent_bone(bn)); e['index'] = i
            try: e['ref'] = tfj(mesh.get_ref_pose_transform(i))
            except Exception as ex: R['ref_err'] = str(ex)[:200]
        bones[s] = e
    smp['bones'] = bones
    return smp
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 6
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            if TAG.startswith('p') and not S.get('swapped'):
                p.call_method('FurinaSwapMid'); S['swapped'] = True; S['t'] = now + 4; return
            p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 'fp'; S['t'] = now + 3; return
        if st == 'fp':
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=rot.yaw))
            if now < S['t']: return
            S['st'] = 'rec'; S['t'] = now + 1.5; return
        if st == 'rec':
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=rot.yaw))
            if now < S['t']: return
            if S['n'] == 0:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/fparms_%s_fp.png"' % (D, TAG))
            smp = record(p, S['n'] == 0); smp['state'] = 'hip'; smp['fov'] = comp(p, 'FPCamera').field_of_view; R['samples'].append(smp); S['n'] += 1; S['t'] = now + 0.35
            if S['n'] >= 5: S['st'] = 'states'; S['si'] = 0; S['t'] = now + 0.2; S['sub'] = 0
            save(); return
        if st == 'states':
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=rot.yaw))
            STS = [('ads', 'FurinaADS'), ('shoulder', 'FurinaShoulder'), ('crouch', 'FurinaCrouch')]
            if S['si'] >= len(STS): S['st'] = 'end'; S['t'] = now + 1.0; return
            nm, cn = STS[S['si']]
            if S['sub'] == 0:
                for _, c2 in STS: p.get_editor_property(c2).set_active(False)
                p.get_editor_property(cn).set_active(True); S['sub'] = 1; S['t'] = now + 2.5; return
            if now < S['t']: return
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/fparms_%s_%s.png"' % (D, TAG, nm))
            smp = record(p, False); smp['state'] = nm; smp['fov'] = comp(p, 'FPCamera').field_of_view; R['samples'].append(smp)
            S['si'] += 1; S['sub'] = 0; S['t'] = now + 0.5
            if S['si'] >= len(STS):
                for _, c2 in STS: p.get_editor_property(c2).set_active(False)
            save(); return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FP_ARMS_POSE armed', TAG)
