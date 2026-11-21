"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 권총에서 손-총 옆면/윗면 캡처.
 FP 카메라가 팔 메시(FurinaMesh)의 부모라 외부 카메라는 불가 -> 카메라 로컬 공간에서 FurinaMesh 를 총 중심 기준으로 회전(손-총 관계는 그대로)해서 옆/위에서 본 모습을 만든다.
 캡처: Data/pside_<태그>_<front|side_r|side_l|top|bottom>.png   기록: Data/lyra_pistol_side_probe_<태그>.json (회전 전 총/뼈 정보)"""
import unreal, json, sys, time, traceback, math
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_pistol_side_probe_%s.json' % TAG
import os
SETS = json.load(open(D + '/side_sets_%s.json' % TAG)) if os.path.exists(D + '/side_sets_%s.json' % TAG) else [{'tag': '', 'vars': {}}]
R = {'tag': TAG, 'shots': [], 'sets': SETS}; S = {'st': 'open', 't': 0, 'vi': 0, 'sub': 0, 'si': 0, 'applied': False}
DBG = True
FB = [('%sFinger%d_%s' % (f, i, sd)) for sd in 'RL' for f in ('Index', 'Middle', 'Ring', 'Little') for i in (1, 2, 3)] + [('Thumb%d_%s' % (i, sd)) for sd in 'RL' for i in (0, 1, 2)] + ['Right-wrist', 'Left-wrist']
DBG_R = ['Right-wrist', 'Thumb1_R', 'Thumb3_R', 'IndexFinger1_R', 'IndexFinger2_R', 'IndexFinger3_R', 'MiddleFinger1_R', 'MiddleFinger2_R', 'MiddleFinger3_R', 'RingFinger1_R', 'RingFinger2_R', 'LittleFinger1_R', 'LittleFinger2_R']
DBG_L = ['Left-wrist', 'Thumb1_L', 'Thumb3_L', 'IndexFinger1_L', 'IndexFinger2_L', 'IndexFinger3_L', 'MiddleFinger1_L', 'MiddleFinger2_L', 'MiddleFinger3_L', 'RingFinger1_L', 'RingFinger2_L', 'LittleFinger1_L', 'LittleFinger2_L']
DIST = 38.0; UPOFF = -2.0; YOFF = 0.0
VIEWS = [('fp', 'FP', 0), ('fpdown', 'FP', 0), ('left', 'X', 0), ('right', '-X', 0), ('top', 'Z', 0)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
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
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 'fp'; S['t'] = now + 2; return
        if st == 'fp' and now >= S['t']:
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=rot.yaw))
            try:
                cands = []
                for ac in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
                    cn = ac.get_class().get_name(); R.setdefault('classes', {}); R['classes'][cn] = R['classes'].get(cn, 0) + 1
                    if cn in ('AtmosphericFog', 'ExponentialHeightFog', 'SkyAtmosphere', 'TextRenderActor', 'StaticMeshActor', 'Note', 'TargetPoint') and ac.root_component is not None: cands.append(ac)
                R['cands'] = [c.get_name() for c in cands[:10]]
                cam = None
                for c in cands:
                    rc = c.root_component
                    try: rc.set_mobility(unreal.ComponentMobility.MOVABLE)
                    except Exception: continue
                    cam = c; break
                R['cam'] = cam.get_name() if cam else None; S['cam'] = cam
                if cam is None: raise Exception('no cam actor')
            except Exception:
                R['spawn_err'] = traceback.format_exc()[-400:]; S['st'] = 'end'; S['t'] = now + 1; save(); return
            S['yaw'] = rot.yaw; S['st'] = 'view'; S['t'] = now + 1; return
        if st == 'view':
            cur = SETS[S['si']]
            if not S['applied']:
                for k, v in cur.get('vars', {}).items(): p.set_editor_property(k, float(v))
                S['applied'] = True; S['t'] = now + 1.5; S['sub'] = 0; S['vi'] = 0
            vlist = [v for v in VIEWS if (not cur.get('views') or v[0] in cur['views'])]
            name, dirv, up = vlist[S['vi']]; cam = S['cam']
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=(-30 if name == 'fpdown' else 0), yaw=S['yaw']))
            rifle = comp(p, 'FurinaRifle'); frame = comp(p, 'FurinaPistolFrame', unreal.StaticMeshComponent)
            o, e, r = unreal.SystemLibrary.get_component_bounds(frame); tf = rifle.get_world_transform()
            import math
            yw = math.radians(S['yaw']); F = unreal.Vector(math.cos(yw), math.sin(yw), 0); Rg = unreal.Vector(-math.sin(yw), math.cos(yw), 0); Up = unreal.Vector(0, 0, 1)
            axes = {'X': Rg * -1, 'Y': F, 'Z': Up}   # X=왼쪽(+), Y=앞, Z=위 (월드 기준, 컨트롤 yaw)
            sg = -1 if dirv[0] == '-' else 1; ax = axes[dirv[-1]] if dirv != 'FP' else None
            C = o + Up * UPOFF + F * YOFF
            pos = C + ax * (sg * DIST) if ax is not None else C
            if False:
                mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent)
                for bn in DBG_R: unreal.SystemLibrary.draw_debug_point(w, mesh.get_socket_location(bn), 5.0, unreal.LinearColor(1, 0, 0, 1), 0.1)
                for bn in DBG_L: unreal.SystemLibrary.draw_debug_point(w, mesh.get_socket_location(bn), 5.0, unreal.LinearColor(0, 1, 0, 1), 0.1)
                fo, fe, fr = unreal.SystemLibrary.get_component_bounds(frame)
                unreal.SystemLibrary.draw_debug_point(w, fo, 6.0, unreal.LinearColor(1, 1, 0, 1), 0.1)
            if ax is not None:
                cam.set_actor_location(pos, False, False); cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos, C), False)
            if now < S['t']: return
            if S['sub'] == 0:
                pc.set_view_target_with_blend(cam if ax is not None else p, 0.0); S['sub'] = 1; S['t'] = now + 2.0; return
            if S['sub'] == 1:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/pside_%s%s_%s.png"' % (D, TAG, cur['tag'], name)); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); bw = {}
                for bn in sorted(set(DBG_R + DBG_L + FB)): v = mesh.get_socket_location(bn); bw[bn] = [round(v.x, 3), round(v.y, 3), round(v.z, 3)]
                bq = {}
                for bn in sorted(set(DBG_R + DBG_L + FB)): qq = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_WORLD).rotation; bq[bn] = [qq.x, qq.y, qq.z, qq.w]
                tfs = {}
                rf_ = comp(p, 'FurinaRifle'); rt_ = rf_.get_world_transform(); tfs['rifle'] = {'loc': [rt_.translation.x, rt_.translation.y, rt_.translation.z], 'q': [rt_.rotation.x, rt_.rotation.y, rt_.rotation.z, rt_.rotation.w]}
                R['pf_vars'] = {k: p.get_editor_property(k) for k in ('FurinaPFLocX', 'FurinaPFLocY', 'FurinaPFLocZ', 'FurinaPFRotP', 'FurinaPFRotY', 'FurinaPFRotR')}
                for cn, cc in (('frame', frame), ('slide', comp(p, 'FurinaPistolSlide', unreal.StaticMeshComponent))):
                    t = cc.get_world_transform(); bb = cc.static_mesh.get_bounding_box(); tfs[cn] = {'loc': [t.translation.x, t.translation.y, t.translation.z], 'q': [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w], 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z], 'bmin': [bb.min.x, bb.min.y, bb.min.z], 'bmax': [bb.max.x, bb.max.y, bb.max.z]}
                R['shots'].append({'name': name, 'set': cur['tag'], 'file': 'pside_%s%s_%s' % (TAG, cur['tag'], name), 'cam': [pos.x, pos.y, pos.z], 'center': [C.x, C.y, C.z], 'frame_center': [o.x, o.y, o.z], 'frame_ext': [e.x, e.y, e.z], 'bones': bw, 'bone_q': bq, 'tf': tfs, 'yaw': S['yaw']})
                S['sub'] = 2; S['t'] = now + 1.0; return
            S['vi'] += 1; S['sub'] = 0; S['t'] = now + 0.3
            if S['vi'] >= len(vlist):
                S['si'] += 1; S['applied'] = False
                if S['si'] >= len(SETS): S['st'] = 'end'
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_SIDE_PROBE armed', TAG)
