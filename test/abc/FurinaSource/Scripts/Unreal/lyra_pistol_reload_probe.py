"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 권총 재장전 측정/캡처.  권총 장착 -> 1인칭 -> 3발 쏨(슬라이드 후퇴 확인) -> FurinaRequestReload(슬로모 0.2) 중 매 틱 기록
 (시간, 잔탄, 장전중, 왼손목/오른손목(소총 기준), 슬라이드 상대 X, 탄창 중심, 곡선), 이벤트 시점 캡처.   -> Data/lyra_pistol_reload_probe_<태그>.json, pistol_reload_<태그>_<이름>.png"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_pistol_reload_probe_%s.json' % TAG
R = {'tag': TAG, 'shots': [], 'fire': [], 'samples': []}; S = {'st': 'open', 't': 0, 'n': 0, 'last': -9}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/pistol_reload_%s_%s.png"' % (D, TAG, name)); R['shots'].append(name)
CAP = [('a', 0.25), ('b', 0.6), ('c', 1.0), ('d', 1.4), ('e', 1.8), ('f', 2.15)]
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
        if st != 'ending' and p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 9
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        gt = unreal.GameplayStatics.get_time_seconds(w)
        if st == 'settle' and now >= S['t']:
            loc0 = p.get_actor_location(); p.set_actor_location(unreal.Vector(loc0.x, loc0.y + 1800.0, loc0.z), False, True)
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(True); rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=rot.yaw)); S['st'] = 'fire'; S['t'] = now + 2; S['n'] = 0; S['t0'] = gt; return
        slide = comp(p, 'FurinaPistolSlide', unreal.StaticMeshComponent); rifle = comp(p, 'FurinaRifle'); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); mag = comp(p, 'FurinaMag', unreal.StaticMeshComponent)
        sx = round(slide.get_editor_property('relative_location').x, 3)
        if st == 'fire':
            R['fire'].append([round(gt - S['t0'], 3), sx, p.get_editor_property('FurinaAmmo')])
            if now >= S['t'] and S['n'] < 3 and now - S['last'] > 0.6:
                p.call_method('FurinaRifleShot'); S['n'] += 1; S['last'] = now
                if S['n'] == 1: unreal.GameplayStatics.set_global_time_dilation(w, 0.2); S['slow_until'] = now + 1.2
            if S['n'] >= 1 and 'slow_until' in S and now > S['slow_until']: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S.pop('slow_until')
            if S['n'] >= 3 and now - S['last'] > 1.0: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'reload'; S['t'] = now + 0.5
            return
        if st == 'reload' and now >= S['t']:
            unreal.GameplayStatics.set_global_time_dilation(w, 0.2); p.call_method('FurinaRequestReload'); S['st'] = 'rec'; S['tg0'] = gt; S['capi'] = 0; return
        if st == 'rec':
            t = gt - S['tg0']; inv = rifle.get_world_transform().inverse()
            def g(v): q = inv.transform_location(v); return [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
            ai = mesh.get_anim_instance()
            row = {'t': round(t, 3), 'ammo': p.get_editor_property('FurinaAmmo'), 'reloading': bool(p.get_editor_property('FurinaReloading')), 'slide_x': sx, 'lw': g(mesh.get_socket_location('Left-wrist')), 'rw': g(mesh.get_socket_location('Right-wrist')),
                   'rl': round(ai.get_curve_value('RifleReload'), 2), 'ms': round(ai.get_curve_value('MagState'), 2), 'mag': g(unreal.SystemLibrary.get_component_bounds(mag)[0]), 'mag_vis': mag.is_visible(), 'mag_mesh': str(mag.static_mesh.get_name()) if mag.static_mesh else None}
            R['samples'].append(row)
            if S['capi'] < len(CAP) and t >= CAP[S['capi']][1]: shot(w, CAP[S['capi']][0]); R['samples'][-1]['cap'] = CAP[S['capi']][0]; S['capi'] += 1
            if t > 2.6 and not row['reloading']:
                unreal.GameplayStatics.set_global_time_dilation(w, 1.0); R['after'] = {'ammo': row['ammo'], 't_end': row['t']}; S['st'] = 'end'; S['t'] = now + 0.5
            elif t > 5: R['after'] = {'timeout': True}; unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'end'; S['t'] = now + 0.5
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
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_RELOAD_PROBE armed', TAG)
