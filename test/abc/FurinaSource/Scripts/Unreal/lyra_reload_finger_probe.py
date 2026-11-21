"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 소총 재장전(빈 탄창 3.0초, 전술 3.3초) 중 왼손 손가락/엄지 뼈의 부모 기준 로컬 회전을 매 틱 기록하고
 뼈별 프레임간 회전 변화량이 큰 순간(튐)을 찾는다. 지정 시각에 캡처.   슬로모 0.15.
 기록: Data/lyra_reload_finger_probe_<태그>.json ('empty' = 빈 탄창, 'tac' = 전술, 각 행: 시각, 뼈별 로컬 쿼터니언, 손목 총 기준 위치, 곡선 HandleBack/HandleFp/RifleReload)
 캡처: Data/rf_<태그>_<empty|tac>_<번호>.png"""
import unreal, json, sys, time, traceback, math
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_reload_finger_probe_%s.json' % TAG
BONES = ['Thumb0_L', 'Thumb1_L', 'Thumb2_L', 'IndexFinger1_L', 'IndexFinger2_L', 'IndexFinger3_L', 'MiddleFinger1_L', 'MiddleFinger2_L', 'MiddleFinger3_L', 'RingFinger1_L', 'RingFinger2_L', 'RingFinger3_L', 'LittleFinger1_L', 'LittleFinger2_L', 'LittleFinger3_L']
R = {'tag': TAG, 'empty': [], 'tac': [], 'shots': []}; S = {'st': 'open', 't': 0, 'n': 0, 'last': -9}
CAPS = {'empty': [0.4, 0.9, 1.4, 1.8, 2.1, 2.3, 2.5, 2.65, 2.8, 2.9, 3.0, 3.05], 'tac': [2.6, 2.9, 3.05, 3.15, 3.25, 3.3]}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def row_for(p, mesh, rifle, t, ai):
    inv = rifle.get_world_transform().inverse(); row = {'t': round(t, 3), 'rl': bool(p.get_editor_property('FurinaReloading'))}
    for b in BONES:
        q = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).rotation; row[b] = [round(q.x, 4), round(q.y, 4), round(q.z, 4), round(q.w, 4)]
    w = inv.transform_location(mesh.get_socket_location('Left-wrist')); row['wrist'] = [round(w.x, 2), round(w.y, 2), round(w.z, 2)]
    for c in ('HandleBack', 'HandleFp', 'RifleReload', 'MagState', 'DbgL', 'DbgR', 'DbgW', 'DbgC'): row[c] = round(ai.get_curve_value(c), 3)
    return row
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
            p.get_editor_property('FurinaFPWanted').set_active(True); rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-20, yaw=rot.yaw))
            S['st'] = 'drain'; S['t'] = now + 3; return
        if st == 'drain':
            if now >= S['t']:
                if p.get_editor_property('FurinaAmmo') > 0:
                    if now - S['last'] > 0.15: p.call_method('FurinaRifleShot'); S['last'] = now
                elif now - S['last'] > 1.5: S['st'] = 'reload_empty'
            return
        if st == 'reload_empty':
            unreal.GameplayStatics.set_global_time_dilation(w, 0.15); p.call_method('FurinaRequestReload'); S['st'] = 'rec_empty'; S['tg0'] = gt; S['ci'] = 0; return
        if st == 'rec_empty':
            t = gt - S['tg0']; R['empty'].append(row_for(p, mesh, rifle, t, mesh.get_anim_instance()))
            if S['ci'] < len(CAPS['empty']) and t >= CAPS['empty'][S['ci']]:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/rf_%s_empty_%02d.png"' % (D, TAG, S['ci'])); R['shots'].append(['empty', S['ci'], round(t, 3)]); S['ci'] += 1
            if t > 3.4 and not R['empty'][-1]['rl']: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'fire_tac'; S['n'] = 0; S['t'] = now + 1.5
            elif t > 6: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'fire_tac'; S['n'] = 0; S['t'] = now + 1
            return
        if st == 'fire_tac' and now >= S['t']:
            if S['n'] < 3 and now - S['last'] > 0.3: p.call_method('FurinaRifleShot'); S['n'] += 1; S['last'] = now
            if S['n'] >= 3 and now - S['last'] > 1.0:
                unreal.GameplayStatics.set_global_time_dilation(w, 0.15); p.call_method('FurinaRequestReload'); S['st'] = 'rec_tac'; S['tg0'] = gt; S['ci'] = 0
            return
        if st == 'rec_tac':
            t = gt - S['tg0']; R['tac'].append(row_for(p, mesh, rifle, t, mesh.get_anim_instance()))
            if S['ci'] < len(CAPS['tac']) and t >= CAPS['tac'][S['ci']]:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/rf_%s_tac_%02d.png"' % (D, TAG, S['ci'])); R['shots'].append(['tac', S['ci'], round(t, 3)]); S['ci'] += 1
            if t > 3.8 and not R['tac'][-1]['rl']: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'end'; S['t'] = now + 0.5
            elif t > 6.5: unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['st'] = 'end'; S['t'] = now + 0.5
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
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_RELOAD_FINGER_PROBE armed', TAG)
