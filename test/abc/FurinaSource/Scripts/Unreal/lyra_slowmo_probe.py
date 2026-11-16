"""Lyra PIE(Play 전에 무장): 모드별(TP / 견착 FurinaShoulder / FP / FP+정조준 FurinaADS) 3발씩, 글로벌 타임 딜레이션 0.01 슬로모션에서 쏘고 총알을 매 프레임 추적.
총알이 사라진 위치와 날아간 거리, 사라진 곳 주변(구 반지름 40) 컴포넌트를 기록한다. 날아간 거리 < 150cm 면 '코앞에 박힘'.  -> Data/lyra_slowmo_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_slowmo_probe.json'
R = {'bullets': []}; S = {'stage': 0, 'ts': 0, 'mi': 0, 'fired': 0, 'last': 0, 'hb': 0, 'hbt': 0, 'live': {}}
MODES = [('TP', False, False, False), ('SHOULDER', False, True, False), ('FP', True, False, False), ('FP_ADS', True, False, True)]
OBJ = [getattr(unreal.ObjectTypeQuery, 'OBJECT_TYPE_QUERY%d' % i) for i in range(1, 7)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def set_mode(pawn, m):
    pawn.get_editor_property('FurinaFPWanted').set_active(m[1]); pawn.get_editor_property('FurinaShoulder').set_active(m[2]); pawn.get_editor_property('FurinaADS').set_active(m[3])
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        rt = time.time(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0); S['hb'] += 1
        if rt - S['hbt'] > 2: S['hbt'] = rt; R['heartbeat'] = [S['hb'], S['stage'], S['mi'], len(R['bullets'])]; save()
        if pawn is None: return
        bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'); mode = MODES[min(S['mi'], len(MODES) - 1)][0]
        # 추적 (매 틱)
        cur = {b.get_name(): b for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc)}
        for n, b in cur.items():
            l = b.get_actor_location()
            if n not in S['live']: S['live'][n] = {'mode': mode, 'name': n, 'spawn': v(l), 'path': [v(l)], 'last': l}
            else: S['live'][n]['last'] = l; (S['live'][n]['path'].append(v(l)) if len(S['live'][n]['path']) < 400 and (S['hb'] % 8 == 0) else None)
        for n in [n for n in S['live'] if n not in cur]:
            d = S['live'].pop(n); l = d.pop('last'); sp = d['spawn']; trav = ((l.x - sp[0]) ** 2 + (l.y - sp[1]) ** 2 + (l.z - sp[2]) ** 2) ** 0.5
            d['death'] = v(l); d['travel'] = round(trav, 1)
            try:
                comps = unreal.SystemLibrary.sphere_overlap_components(w, l, 40.0, OBJ, unreal.PrimitiveComponent, [pawn])
                comps = comps if isinstance(comps, (list, tuple)) and (not comps or not isinstance(comps[0], bool)) else comps[1]
                d['near'] = [c.get_owner().get_name() + '/' + c.get_name() for c in comps][:8]
            except Exception as e: d['near'] = 'ERR ' + str(e)[:60]
            d['path'] = d['path'][:3] + d['path'][-3:]; R['bullets'].append(d)
        # 단계
        if S['stage'] == 0: S['stage'] = 1; S['ts'] = rt; set_mode(pawn, MODES[0])
        elif S['stage'] == 1 and rt - S['ts'] > 6:            # 모드 안정화 후 슬로모션 시작
            unreal.GameplayStatics.set_global_time_dilation(w, 0.01); S['stage'] = 2; S['fired'] = 0; S['last'] = rt; S['ts'] = rt
        elif S['stage'] == 2:
            if S['fired'] < 3 and rt - S['last'] > 1.5: S['last'] = rt; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            if S['fired'] >= 3 and rt - S['last'] > 5 and not S['live']:
                unreal.GameplayStatics.set_global_time_dilation(w, 1.0); S['mi'] += 1; S['ts'] = rt
                if S['mi'] >= len(MODES): S['stage'] = 3
                else: set_mode(pawn, MODES[S['mi']]); S['stage'] = 1
            elif rt - S['ts'] > 60: R['timeout'] = [mode, list(S['live'])]; S['live'].clear()
        elif S['stage'] == 3:
            S['stage'] = 9; unreal.GameplayStatics.set_global_time_dilation(w, 1.0); set_mode(pawn, MODES[0]); save(); print('LYRA_SLOWMO_PROBE', len(R['bullets'])); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.GameplayStatics.set_global_time_dilation(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 1.0)
        except Exception: pass
        unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_SLOWMO_PROBE armed')
