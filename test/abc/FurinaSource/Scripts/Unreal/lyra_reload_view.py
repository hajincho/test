"""Lyra PIE(Play 전에 무장): 푸리나 폰이 있으면(없으면 수동 possess) 6발 쏜 뒤 재장전을 요청해 **게임 시간** 기준으로 기록 + HighResShot.
3인칭 한 번, 이어서 1인칭(FurinaFPWanted 켬) 한 번. 기록: t(게임초), FurinaReloading, FurinaAmmo, MagState 커브, FurinaMagLast, 왼손목의 총 기준 위치(X왼쪽,Y앞,Z위 cm) 의 재장전 전 대비 변화.
-> FurinaSource/Data/lyra_reload_view.json (옆모습 확인용 변형: 재장전 시작 때 폰을 90도 돌려 카메라가 옆에서 보게 함, TP 한 번만) ; 스크린샷은 Saved/Screenshots/WindowsEditor/"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_reload_view.json'
R = {'runs': []}; S = {'t0': time.time(), 'stage': 0, 'ts': 0, 'run': None, 'shots': [], 'hb': 0, 'hbt': 0}
import sys
SIDE_YAW = float(sys.argv[-1]) if sys.argv[-1].replace('-','',1).replace('.','',1).isdigit() else 90.0
SHOTS = [0.02, 0.4, 0.7, 1.0, 1.25, 1.5, 1.75, 2.0, 2.3, 2.6, 2.9]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def comp(pawn, name, cls=unreal.SceneComponent):
    for c in pawn.get_components_by_class(cls):
        if c.get_name() == name: return c
    return None
def gun_rel(pawn, loc):
    rifle = comp(pawn, 'FurinaRifle')
    if rifle is None: return None
    d = rifle.get_world_transform().inverse_transform_location(loc); return [d.x, d.y, d.z]
def tick(dt):
    try:
        S['hb'] += 1
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if time.time() - S['hbt'] > 2.0:
            S['hbt'] = time.time(); R['heartbeat'] = [S['hb'], S['stage'], w is not None, None if w is None else round(unreal.GameplayStatics.get_time_seconds(w), 2)]; save()
        if w is None: return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0); now = unreal.GameplayStatics.get_time_seconds(w)
        if pawn is None:
            if S.get('first_wait') is None: S['first_wait'] = now
            if now - S['first_wait'] > 8:
                free = [p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn) if p.get_controller() is None]
                if free: unreal.GameplayStatics.get_player_controller(w, 0).possess(free[0]); R['manual_possess'] = True
            return
        if S['stage'] == 0:
            S['stage'] = 1; S['ts'] = now; R['pawn'] = pawn.get_class().get_name(); R['loc'] = str(pawn.get_actor_location())
        elif S['stage'] == 1 and now - S['ts'] > 4: S['fired'] = 0; S['lastshot'] = -9; S['stage'] = 15
        elif S['stage'] in (15, 35):
            if S['fired'] < 6 and now - S['lastshot'] > 0.25: S['lastshot'] = now; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            if S['fired'] >= 6 and now - S['lastshot'] > 1.0:
                mode = 'TP' if S['stage'] == 15 else 'FP'; mesh = comp(pawn, 'FurinaMesh', unreal.SkeletalMeshComponent)
                R['ammo_before_reload_' + mode] = pawn.get_editor_property('FurinaAmmo')
                pawn.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=pawn.get_actor_rotation().yaw + SIDE_YAW), False)
                S['run'] = {'mode': mode, 'samples': [], 'wrist0': gun_rel(pawn, mesh.get_socket_location('Left-wrist'))}; S['req'] = now; S['shots'] = list(SHOTS)
                unreal.GameplayStatics.set_global_time_dilation(w, 0.15); pawn.call_method('FurinaRequestReload'); S['stage'] = 2 if mode == 'TP' else 4
        elif S['stage'] in (2, 4):
            t = now - S['req']; mesh = comp(pawn, 'FurinaMesh', unreal.SkeletalMeshComponent); ai = mesh.get_anim_instance() if mesh else None
            mag = ai.get_curve_value('MagState') if ai else None; wr = gun_rel(pawn, mesh.get_socket_location('Left-wrist')); w0 = S['run']['wrist0']
            dl = [round(wr[i] - w0[i], 1) for i in range(3)] if wr and w0 else None
            S['run']['samples'].append([round(t, 3), bool(pawn.get_editor_property('FurinaReloading')), pawn.get_editor_property('FurinaAmmo'), None if mag is None else round(mag, 2), pawn.get_editor_property('FurinaMagLast'), dl])
            if S['shots'] and t >= S['shots'][0]:
                S['shots'].pop(0); unreal.SystemLibrary.execute_console_command(w, 'HighResShot 3'); S['run'].setdefault('shot_times', []).append(round(t, 2))
            if t > 3.6 or (S['stage'] == 2 and t > 3.6):
                s = S['run']['samples']; S['run']['reloading_false_at'] = next((x[0] for x in s if x[0] > 0.3 and not x[1]), None)
                S['run']['ammo_full_at'] = next((x[0] for x in s if x[2] == 20), None)
                R['runs'].append(S['run']); save(); unreal.GameplayStatics.set_global_time_dilation(w, 1.0)
                if S['stage'] == 2:
                    S['stage'] = 9; R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
                else:
                    pawn.get_editor_property('FurinaFPWanted').set_active(False); S['stage'] = 9; unreal.unregister_slate_post_tick_callback(S['h'])
        elif S['stage'] == 3 and now - S['ts'] > 3: S['fired'] = 0; S['lastshot'] = -9; S['stage'] = 35
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_RELOAD_PROBE armed')
