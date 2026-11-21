"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1 백그라운드): 1인칭 전용 팔 확인.
 1인칭 소총에서 상태별 화면 캡처 + 매 틱 기록(FP 팔 L/R 보이기, 본체 팔 숨김, 재장전, LHold, 본체 왼손목-구운 위치 거리).
 캡처: Data/fpa_<태그>_<상태>.png    기록: Data/lyra_fp_arms_probe_<태그>.json"""
import unreal, json, sys, time, traceback, math
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_fp_arms_probe_%s.json' % TAG
BK = json.load(open(D + '/fp_arms_bake_a1.json')); LW = BK['wrist_rifle_local']['Left-wrist']
R = {'tag': TAG, 'ticks': [], 'shots': [], 'events': []}; S = {'st': 'open', 't': 0, 'i': 0, 'sub': 0, 't0': None}
# (이름, 동작, 대기초, 피치)
STEPS = [('hip', None, 1.5, 0), ('hipdown', None, 1.2, -35), ('hipup', None, 1.2, 30),
         ('ads', 'ads_on', 2.0, 0), ('shoulder', 'shoulder_on', 2.0, 0), ('hip2', 'aim_off', 1.8, 0),
         ('walk', 'walk', 1.6, 0), ('fire', 'fire', 0.12, 0),
         ('rl_a', 'reload', 0.5, -10), ('rl_b', None, 0.6, -10), ('rl_c', None, 0.7, -10), ('rl_end', 'wait_rl', 0.0, -10),
         ('side_left', 'side:X', 1.5, 0), ('side_right', 'side:-X', 1.2, 0), ('side_top', 'side:Z', 1.2, 0), ('side_back', 'side:-Y', 1.2, 0),
         ('pistol', 'pistol', 4.0, 0), ('tp', 'tp', 3.0, -8)]
PIST = TAG.startswith('p')
if PIST:
    STEPS = [('hip', None, 1.5, 0), ('hipdown', None, 1.2, -35), ('hipup', None, 1.2, 30), ('ads', 'ads_on', 2.0, 0), ('hip2', 'aim_off', 1.8, 0),
             ('walk', 'walk', 1.6, 0), ('fire', 'fire', 0.12, 0), ('rl_a', 'reload', 0.5, -10), ('rl_b', None, 0.6, -10), ('rl_c', None, 0.6, -10), ('rl_end', 'wait_rl', 0.0, -10),
             ('side_left', 'side:X', 1.5, 0), ('side_right', 'side:-X', 1.2, 0), ('side_top', 'side:Z', 1.2, 0), ('side_back', 'side:-Y', 1.2, 0), ('side_front', 'side:Y', 1.2, 0), ('tp', 'tp', 3.0, -8)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def status(p):
    mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); rf = comp(p, 'FurinaRifle'); al = comp(p, 'FurinaFPArmL', unreal.StaticMeshComponent); ar = comp(p, 'FurinaFPArmR', unreal.StaticMeshComponent)
    lw = mesh.get_socket_location('Left-wrist'); loc = unreal.MathLibrary.inverse_transform_location(rf.get_world_transform(), lw)
    d = math.sqrt((loc.x - LW[0]) ** 2 + (loc.y - LW[1]) ** 2 + (loc.z - LW[2]) ** 2)
    pl_ = comp(p, 'FurinaFPPistArmL', unreal.StaticMeshComponent); pr_ = comp(p, 'FurinaFPPistArmR', unreal.StaticMeshComponent)
    return {'parmL': pl_.is_visible() if pl_ else None, 'parmR': pr_.is_visible() if pr_ else None, 'armL': al.is_visible() if al else None, 'armR': ar.is_visible() if ar else None, 'hidL': mesh.is_bone_hidden_by_name('Left-arm'), 'hidR': mesh.is_bone_hidden_by_name('Right-arm'),
            'rl': bool(p.get_editor_property('FurinaReloading')), 'hold': round(p.get_editor_property('FurinaFPArmLHold'), 3), 'dL': round(d, 3),
            'fp': comp(p, 'FPCamera').is_active(), 'pistol': p.get_editor_property('FurinaPistolOn').is_active()}
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
        if p is None: return
        gt = unreal.GameplayStatics.get_time_seconds(w)
        if S['t0'] is not None and st not in ('end', 'ending'):
            e = status(p); e['t'] = round(gt - S['t0'], 3); e['step'] = STEPS[S['i']][0] if S['i'] < len(STEPS) else 'x'; R['ticks'].append(e)
        if st == 'settle' and now >= S['t'] and PIST and not S.get('swapped'):
            p.call_method('FurinaSwapMid'); S['swapped'] = True; S['t'] = now + 4; return
        if st == 'settle' and now >= S['t']:
            R['before_fp'] = status(p)
            p.get_editor_property('FurinaFPWanted').set_active(True); S['yaw'] = pc.get_control_rotation().yaw; S['st'] = 'seq'; S['t'] = now + 2.5; S['t0'] = gt
            for ac in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                if ac.get_class().get_name() in ('AtmosphericFog', 'ExponentialHeightFog', 'SkyAtmosphere') and ac.root_component is not None:
                    try: ac.root_component.set_mobility(unreal.ComponentMobility.MOVABLE); S['cam'] = ac; break
                    except Exception: pass
            return
        if st == 'seq':
            name, act, wait, pitch = STEPS[S['i']]
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=S['yaw']))
            if S['sub'] == 0:
                if now < S['t']: return
                if act == 'ads_on': p.get_editor_property('FurinaADS').set_active(True)
                elif act == 'shoulder_on': p.get_editor_property('FurinaADS').set_active(False); p.get_editor_property('FurinaShoulder').set_active(True)
                elif act == 'aim_off': p.get_editor_property('FurinaShoulder').set_active(False); p.get_editor_property('FurinaADS').set_active(False)
                elif act == 'fire': p.call_method('FurinaRifleShot')
                elif act == 'reload': p.call_method('FurinaRequestReload'); R['events'].append(['reload', round(gt - S['t0'], 3)])
                elif act == 'pistol': p.call_method('FurinaSwapMid')
                elif act == 'tp': p.get_editor_property('FurinaFPWanted').set_active(False)
                S['sub'] = 1; S['t'] = now + wait; S['tw'] = now; return
            if act == 'walk':
                yw = math.radians(S['yaw']); p.add_movement_input(unreal.Vector(math.cos(yw), math.sin(yw), 0), 1.0, False)
            if act == 'wait_rl':
                stt = status(p)
                if (stt['rl'] or not stt['armL']) and now - S['tw'] < 8: return
                R['events'].append(['left_back', round(gt - S['t0'], 3), stt])
            cam = S.get('cam')
            if act and act.startswith('side:') and cam is not None:
                rf = comp(p, 'FurinaPistolFrame', unreal.StaticMeshComponent) if PIST else comp(p, 'FurinaRifle'); o, ex, rr = unreal.SystemLibrary.get_component_bounds(rf)
                yw = math.radians(S['yaw']); F = unreal.Vector(math.cos(yw), math.sin(yw), 0); Rg = unreal.Vector(-math.sin(yw), math.cos(yw), 0); Up = unreal.Vector(0, 0, 1)
                axes = {'X': Rg * -1, 'Y': F, 'Z': Up}; d = act.split(':')[1]; sg = -1 if d[0] == '-' else 1; ax = axes[d[-1]]
                C = o + (F * (-3.0) + Up * (-3.0) if PIST else F * (-8.0)); pos = C + ax * (sg * (40.0 if PIST else 70.0)) + (Up * 0.5 if d[-1] == 'Z' else Up * 0)
                cam.set_actor_location(pos, False, False); cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos, C), False)
                if S['sub'] == 1: pc.set_view_target_with_blend(cam, 0.0); S['sub'] = 2
            if now < S['t']: return
            if S['sub'] in (1, 2):
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/fpa_%s_%s.png"' % (D, TAG, name))
                R['shots'].append([name, round(gt - S['t0'], 3), status(p)]); S['sub'] = 3; S['t'] = now + 0.25; save(); return
            if act and act.startswith('side:') and (S['i'] + 1 >= len(STEPS) or not (STEPS[S['i'] + 1][1] or '').startswith('side:')): pc.set_view_target_with_blend(p, 0.0)
            S['i'] += 1; S['sub'] = 0; S['t'] = now + 0.1
            if S['i'] >= len(STEPS): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FP_ARMS_PROBE armed', TAG)
