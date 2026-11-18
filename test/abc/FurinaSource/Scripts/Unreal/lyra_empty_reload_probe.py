"""Lyra 에디터(`py <파일> [yaw90|yawm90|fp] [태그]`, PIE 중지 상태): 오버뷰 맵 PIE 에서 노리쇠 후퇴와 긴급 재장전을 측정/캡처한다.
 1) 단발 5발(0.25초 간격)을 쏘며 노리쇠(FurinaBolt) 상대 Y 를 매 틱 기록 (피크, 복귀)
 2) 잔탄 0 까지 쏜 뒤 1.5초 대기: 노리쇠 걸림 위치 기록 + 캡처
 3) FurinaRequestReload (슬로모 0.15): 매 틱 (시간, 잔탄, FurinaReloading, MagState/BoltBack 곡선, 노리쇠 Y, 왼손목/탄창 중심(총 기준), 몽타주 위치) 기록, 이벤트 시점 캡처
    -> 완료 후 잔탄, 노리쇠 위치 기록
 4) 3발 쏜 뒤 다시 재장전(잔탄>0 = 일반 재장전): 걸린 시간(잔탄이 차는 시점)과 노리쇠가 움직이지 않는지 기록
 캡처: Data/empty_reload_<태그>_<이름>.png   기록: Data/lyra_empty_reload_probe_<태그>.json
 시점: yaw90 / yawm90 = 3인칭에서 카메라를 폰 기준 +90/-90도로(옆모습), fp = 1인칭 + 아래 보기"""
import unreal, json, sys, time, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]
VIEW = ARGS[0] if ARGS and ARGS[0] in ('yaw90', 'yawm90', 'fp') else 'yaw90'; TAG = ARGS[-1] if ARGS and ARGS[-1] not in ('yaw90', 'yawm90', 'fp') else VIEW
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_empty_reload_probe_%s.json' % TAG
R = {'view': VIEW, 'shots': [], 'phase1': [], 'samples': [], 'normal': []}; S = {'st': 'open', 't': 0, 'n': 0, 'last': -9}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/empty_reload_%s_%s.png"' % (D, TAG, name)); R['shots'].append(name)
CAP = [('a_approach', 0.30), ('b_grab', 0.55), ('c_down', 0.85), ('d_newmag', 1.05), ('e_seat', 1.25), ('f_reach', 1.40), ('g_grab', 1.50), ('h_pulled', 1.62), ('i_pulled2', 1.70), ('j_release', 1.75), ('k_after', 1.83), ('l_return', 1.95)]
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
        if st in ('ending', 'done'):
            pass
        elif p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None and comp(p, 'FurinaHandle') is not None: S['st'] = 'settle'; S['t'] = now + 9
            elif now >= S['t']: R['error'] = 'no pawn/bolt'; S['st'] = 'end'
            return
        gt = unreal.GameplayStatics.get_time_seconds(w); bolt = comp(p, 'FurinaBolt'); hnd = comp(p, 'FurinaHandle'); rifle = comp(p, 'FurinaRifle'); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); mag = comp(p, 'FurinaMag', unreal.StaticMeshComponent)
        by = round(bolt.get_editor_property('relative_location').y, 3)
        if VIEW != 'fp' and 'cyaw' in S and st not in ('settle',): p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['cyaw'] + (90 if VIEW == 'yaw90' else -90)), False)   # 폰을 카메라 기준 옆으로 세워 옆모습을 찍는다(카메라는 컨트롤 회전 그대로)
        if st == 'settle' and now >= S['t']:
            loc0 = p.get_actor_location(); p.set_actor_location(unreal.Vector(loc0.x, loc0.y + 1800.0, loc0.z), False, True)   # 마네킹이 없는 빈 바닥으로 옮김
            cam = comp(p, 'FPCamera')
            if cam is not None:
                ci = cam.get_world_transform().inverse(); rl = rifle.get_world_transform().translation; q = ci.transform_location(rl); R['fp_gun_rel_cam'] = [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
                ri = rifle.get_world_transform().inverse(); la = ri.transform_location(mesh.get_socket_location('Left-arm')); lw = ri.transform_location(mesh.get_socket_location('Left-wrist')); R['rest_left'] = {'arm': [round(la.x, 2), round(la.y, 2), round(la.z, 2)], 'wrist': [round(lw.x, 2), round(lw.y, 2), round(lw.z, 2)], 'reach': round((la - lw).length(), 2)}
            R['bolt_comp'] = {'visible': bolt.is_visible(), 'mesh': str(bolt.static_mesh), 'start_y': by, 'ammo': p.get_editor_property('FurinaAmmo')}
            if VIEW == 'fp': p.get_editor_property('FurinaFPWanted').set_active(True); rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=rot.yaw))
            else:
                p.get_editor_property('FurinaFPWanted').set_active(False); S['cyaw'] = p.get_actor_rotation().yaw; pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=S['cyaw']))
            S['st'] = 'fire1'; S['t'] = now + 3; S['n'] = 0; S['t0'] = gt; return
        if st == 'fire1':
            R['phase1'].append([round(gt - S['t0'], 3), by, p.get_editor_property('FurinaAmmo')])
            if now >= S['t'] and S['n'] < 5 and now - S['last'] > 0.25: p.call_method('FurinaRifleShot'); S['n'] += 1; S['last'] = now; S['mark'] = len(R['phase1'])
            if S['n'] >= 5 and now - S['last'] > 1.0: S['st'] = 'drain'
            return
        if st == 'drain':
            if p.get_editor_property('FurinaAmmo') > 0:
                if now - S['last'] > 0.2: p.call_method('FurinaRifleShot'); S['last'] = now
            elif now - S['last'] > 1.5:
                R['locked'] = {'bolt_y': by, 'ammo': p.get_editor_property('FurinaAmmo')}; shot(w, 'locked'); S['st'] = 'reload'; S['t'] = now + 1.0
            return
        if st == 'reload' and now >= S['t']:
            unreal.GameplayStatics.set_global_time_dilation(w, 0.15); p.call_method('FurinaRequestReload'); S['st'] = 'rec'; S['tg0'] = gt; S['capi'] = 0; return
        if st == 'rec':
            t = gt - S['tg0']; inv = rifle.get_world_transform().inverse()
            def g(v): q = inv.transform_location(v); return [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
            ai = mesh.get_anim_instance()
            row = {'t': round(t, 3), 'ammo': p.get_editor_property('FurinaAmmo'), 'reloading': bool(p.get_editor_property('FurinaReloading')), 'ms': round(ai.get_curve_value('MagState'), 2), 'bb': round(ai.get_curve_value('BoltBack'), 2), 'bolt_y': by,
                   'rp': round(unreal.KismetMaterialLibrary.get_scalar_parameter_value(w, unreal.load_asset('/Game/Furina/UI/MPC_FurinaHUD'), 'ReloadP'), 3), 'wrist': g(mesh.get_socket_location('Left-wrist')), 'mid1': g(mesh.get_socket_location('MiddleFinger1_L')), 'idx3': g(mesh.get_socket_location('IndexFinger3_L')), 'Larm': g(mesh.get_socket_location('Left-arm')), 'Lelb': g(mesh.get_socket_location('Left-elbow')), 'Rarm': g(mesh.get_socket_location('Right-arm')), 'hy': round(hnd.get_editor_property('relative_location').y, 3), 'mag': g(unreal.SystemLibrary.get_component_bounds(mag)[0]), 'mag_vis': mag.is_visible()}
            R['samples'].append(row)
            if S['capi'] < len(CAP) and t >= CAP[S['capi']][1]: shot(w, CAP[S['capi']][0]); R['samples'][-1]['cap'] = CAP[S['capi']][0]; S['capi'] += 1
            if t > 2.4 and not row['reloading']:
                unreal.GameplayStatics.set_global_time_dilation(w, 1.0); R['after'] = {'ammo': row['ammo'], 'bolt_y': by, 't_end': row['t']}; S['st'] = 'normal_fire'; S['n'] = 0; S['t'] = now + 1.5
            elif t > 4.5: R['after'] = {'timeout': True}; unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'normal_fire'; S['n'] = 0; S['t'] = now + 1
            return
        if st == 'normal_fire' and now >= S['t']:
            if S['n'] < 3 and now - S['last'] > 0.3: p.call_method('FurinaRifleShot'); S['n'] += 1; S['last'] = now
            if S['n'] >= 3 and now - S['last'] > 1.0:
                R['normal_ammo_before'] = p.get_editor_property('FurinaAmmo'); p.call_method('FurinaRequestReload'); S['st'] = 'normal_rec'; S['tg0'] = gt
            return
        if st == 'normal_rec':
            inv = rifle.get_world_transform().inverse()
            def g(v): q = inv.transform_location(v); return [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
            t = gt - S['tg0']; R['normal'].append([round(t, 3), p.get_editor_property('FurinaAmmo'), by, round(mesh.get_anim_instance().get_curve_value('BoltBack'), 2)])
            row = {'t': round(t, 3), 'rl': bool(p.get_editor_property('FurinaReloading'))}
            for b in ('Thumb0_L', 'Thumb1_L', 'Thumb2_L', 'Thumb3_L', 'IndexFinger1_L', 'Left-wrist'):
                tr = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_COMPONENT); r = tr.rotation.rotator(); row[b] = [round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)]
            row['rp'] = round(unreal.KismetMaterialLibrary.get_scalar_parameter_value(w, unreal.load_asset('/Game/Furina/UI/MPC_FurinaHUD'), 'ReloadP'), 3); row['hy'] = round(hnd.get_editor_property('relative_location').y, 3); row['bolt_y'] = by; row['wrist'] = g(mesh.get_socket_location('Left-wrist')); row['idx3'] = g(mesh.get_socket_location('IndexFinger3_L'))
            R.setdefault('thumb', []).append(row)
            if t > 4.6 or (t > 3.9 and not p.get_editor_property('FurinaReloading')): R['normal_done_t'] = round(t, 2); S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.GameplayStatics.set_global_time_dilation(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 1.0)
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_EMPTY_RELOAD_PROBE armed', VIEW, TAG)
