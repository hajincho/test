"""Lyra 에디터(`py <파일> [fp|tp] [태그]`, PIE 중지 상태): 일반 재장전(잔탄 > 0)이 끝나고 왼손이 총열(핸드가드)로 돌아올 때 엄지 움직임을 찍는다.
 3발 쏜 뒤 FurinaRequestReload, 슬로모 0.1로 지정 시각마다 캡처하고 엄지/검지/손목의 손목 기준 상대 위치(총 기준 좌표와 손목 로컬)를 기록.
 캡처: Data/thumb_<태그>_<번호>.png   기록: Data/lyra_thumb_probe_<태그>.json"""
import unreal, json, sys, time, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]
VIEW = ARGS[0] if ARGS and ARGS[0] in ('fp', 'tp') else 'fp'; TAG = ARGS[-1] if ARGS and ARGS[-1] not in ('fp', 'tp') else VIEW
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_thumb_probe_%s.json' % TAG
R = {'view': VIEW, 'samples': [], 'shots': []}; S = {'st': 'open', 't': 0, 'n': 0, 'last': -9}
CAPT = [2.60, 2.75, 2.82, 2.86, 2.90, 2.94, 2.98, 3.02, 3.10, 3.25]
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
        if st not in ('ending', 'done') and p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 9
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        gt = unreal.GameplayStatics.get_time_seconds(w); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent) if p else None; rifle = comp(p, 'FurinaRifle') if p else None
        if st == 'settle' and now >= S['t']:
            loc0 = p.get_actor_location(); p.set_actor_location(unreal.Vector(loc0.x, loc0.y + 1800.0, loc0.z), False, True)
            if VIEW == 'fp': p.get_editor_property('FurinaFPWanted').set_active(True); rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-28, yaw=rot.yaw))
            S['st'] = 'fire'; S['t'] = now + 3; S['n'] = 0; return
        if st == 'fire' and 'rest_thumb' not in R:
            R['rest_thumb'] = {}
            for b in ('Thumb0_L', 'Thumb1_L', 'Thumb2_L'):
                q = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).rotation; R['rest_thumb'][b] = [q.x, q.y, q.z, q.w]
            json.dump(R['rest_thumb'], open(D + '/thumb_rest.json', 'w'))
        if st == 'fire':
            if now >= S['t'] and S['n'] < 3 and now - S['last'] > 0.3: p.call_method('FurinaRifleShot'); S['n'] += 1; S['last'] = now
            if S['n'] >= 3 and now - S['last'] > 1.0: S['st'] = 'reload'
            return
        if st == 'reload':
            unreal.GameplayStatics.set_global_time_dilation(w, 0.1); p.call_method('FurinaRequestReload'); S['tg0'] = gt; S['ci'] = 0; S['st'] = 'rec'; return
        if st == 'rec':
            t = gt - S['tg0']; inv = rifle.get_world_transform().inverse(); row = {'t': round(t, 3), 'rl': bool(p.get_editor_property('FurinaReloading'))}
            wt = mesh.get_socket_transform('Left-wrist', unreal.RelativeTransformSpace.RTS_WORLD); winv = wt.inverse()
            for b in ('Thumb0_L', 'Thumb1_L', 'Thumb2_L', 'Thumb3_L', 'IndexFinger1_L', 'IndexFinger3_L', 'Left-wrist'):
                loc = mesh.get_socket_location(b); q = inv.transform_location(loc); wl = winv.transform_location(loc)
                row[b] = [round(q.x, 2), round(q.y, 2), round(q.z, 2)]; row[b + '_w'] = [round(wl.x, 2), round(wl.y, 2), round(wl.z, 2)]
            for b in ('Thumb0_L', 'Thumb1_L', 'Thumb2_L', 'IndexFinger1_L', 'MiddleFinger1_L'):
                tr = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD); dw = unreal.MathLibrary.transform_direction(tr, unreal.Vector(0.0, -1.0, 0.0)); dl = unreal.MathLibrary.inverse_transform_direction(wt, dw)
                up = unreal.MathLibrary.transform_direction(tr, unreal.Vector(0.0, 0.0, 1.0)); ul = unreal.MathLibrary.inverse_transform_direction(wt, up)
                row[b + '_dir'] = [round(dl.x, 3), round(dl.y, 3), round(dl.z, 3)]; row[b + '_up'] = [round(ul.x, 3), round(ul.y, 3), round(ul.z, 3)]
            R['samples'].append(row)
            if S['ci'] < len(CAPT) and t >= CAPT[S['ci']]:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/thumb_%s_%02d.png"' % (D, TAG, S['ci'])); R['shots'].append([S['ci'], round(t, 3)]); S['ci'] += 1
            if t > 3.5: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6
            return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.GameplayStatics.set_global_time_dilation(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 1.0)
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_THUMB_PROBE armed', VIEW, TAG)
