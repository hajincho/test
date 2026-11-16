"""Lyra PIE(Play 전에 무장): 한 프레임에 여러 발이 생기면 총알끼리 충돌해 총구에서 막히는지 확인. 글로벌 타임 딜레이션 0.01 슬로모션으로 총알을 매 틱 추적.
그룹: 프레임당 1발 x4, 프레임당 3발 x4 (총 16발). 총알마다 생성 위치 / 사라진 위치 / 날아간 거리 / 같은 그룹 몇 번째인지 기록. 날아간 거리 < 150cm = 총구 근처에서 막힘.
-> Data/lyra_samefame_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_samefame_probe.json'
R = {'groups': [], 'bullets': []}; S = {'stage': 0, 'ts': 0, 'g': 0, 'hb': 0, 'hbt': 0, 'live': {}, 'cur': None, 'order': 0}
PLAN = [1] * 4 + [3] * 4
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        rt = time.time(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0); S['hb'] += 1
        if rt - S['hbt'] > 2: S['hbt'] = rt; R['heartbeat'] = [S['hb'], S['stage'], S['g'], len(R['bullets'])]; save()
        if pawn is None: return
        bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
        cur = {b.get_name(): b for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc)}
        for n, b in cur.items():
            l = b.get_actor_location()
            if n not in S['live']: S['live'][n] = {'name': n, 'group': S['cur'], 'spawn': v(l), 'last': l, 'idx': S['order']}; S['order'] += 1
            else: S['live'][n]['last'] = l
        for n in [n for n in S['live'] if n not in cur]:
            d = S['live'].pop(n); l = d.pop('last'); sp = d['spawn']; d['death'] = v(l); d['travel'] = round(((l.x - sp[0]) ** 2 + (l.y - sp[1]) ** 2 + (l.z - sp[2]) ** 2) ** 0.5, 1); R['bullets'].append(d)
        if S['stage'] == 0: S['stage'] = 1; S['ts'] = rt; pawn.get_editor_property('FurinaFPWanted').set_active(True)
        elif S['stage'] == 1 and rt - S['ts'] > 6: unreal.GameplayStatics.set_global_time_dilation(w, 0.01); S['stage'] = 2; S['ts'] = rt
        elif S['stage'] == 2 and rt - S['ts'] > 1.0 and not S['live']:
            if S['g'] >= len(PLAN): S['stage'] = 3; S['ts'] = rt; return
            n = PLAN[S['g']]; S['cur'] = S['g']; R['groups'].append({'g': S['g'], 'shots_in_frame': n})
            for _ in range(n): pawn.call_method('FurinaRifleShot')
            S['g'] += 1; S['ts'] = rt
        elif S['stage'] == 3:
            unreal.GameplayStatics.set_global_time_dilation(w, 1.0)
            for g in R['groups']:
                bs = [b for b in R['bullets'] if b['group'] == g['g']]; g['travels'] = [b['travel'] for b in sorted(bs, key=lambda b: b['idx'])]
            S['stage'] = 9; save(); print('LYRA_SAMEFRAME done'); unreal.unregister_slate_post_tick_callback(S['h'])
        elif S['stage'] == 2 and rt - S['ts'] > 90: R['timeout'] = True; S['stage'] = 3
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.GameplayStatics.set_global_time_dilation(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 1.0)
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_SAMEFRAME armed')
