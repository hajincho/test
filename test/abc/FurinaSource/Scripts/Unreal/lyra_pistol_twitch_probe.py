"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 1인칭 권총 모드에서 손가락 뼈의 부모 기준 로컬 회전을 매 틱 기록해 꿈틀거림(구간별 최대 변화량/속도)을 측정한다.
 구간: idle(3s) -> look(3s, 시선 위아래/좌우) -> walk(3s) -> sprint-ish(3s, 이동 입력+ 큰 입력) -> jump(2s) -> fire(발사 3회) -> idle2(2s)
 -> Data/lyra_pistol_twitch_probe_<태그>.json  (stages: 구간별 {bone: [max_dev_from_idle_deg, max_speed_deg_per_s]} )"""
import unreal, json, sys, time, math, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_pistol_twitch_probe_%s.json' % TAG
BONES = [('Thumb%d_%s' % (i, s)) for s in 'RL' for i in range(4)] + [('%sFinger%d_%s' % (f, i, s)) for s in 'RL' for f in ('Index', 'Middle', 'Ring', 'Little') for i in (1, 2, 3)]
STAGES = [('settle', 2.5), ('idle', 3.0), ('look', 3.0), ('walk', 3.0), ('walkfast', 1.5), ('jump', 2.0), ('fire', 3.0), ('reload', 3.0), ('idle2', 2.0)]
R = {'tag': TAG}; S = {'st': 'open', 't': 0, 'si': -1, 'ts': 0, 'rec': []}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def qv(q): return (q.x, q.y, q.z, q.w)
def ang(a, b):
    d = abs(sum(x * y for x, y in zip(a, b))); d = min(1.0, d); return math.degrees(2 * math.acos(d))
def analyze():
    rec = S['rec']; out = {}
    idle = [r for r in rec if r['stage'] == 'idle' and r['t'] > 1.0]
    ref = {}
    for b in BONES:
        qs = [r['q'][b] for r in idle]
        ref[b] = qs[len(qs) // 2] if qs else None
    for name, _ in STAGES:
        rs = [r for r in rec if r['stage'] == name]; st = {}
        for b in BONES:
            if ref[b] is None or len(rs) < 3: continue
            dev = max(ang(r['q'][b], ref[b]) for r in rs)
            spd = 0.0
            for a, c in zip(rs, rs[1:]):
                dt = max(1e-3, c['t'] - a['t']); spd = max(spd, ang(a['q'][b], c['q'][b]) / dt)
            st[b] = [round(dev, 2), round(spd, 1)]
        out[name] = {'n': len(rs), 'bones': st, 'worst_dev': max([v[0] for v in st.values()] or [0]), 'worst_speed': max([v[1] for v in st.values()] or [0])}
    R['stages'] = out
    R['consts'] = {b: [round(x, 6) for x in ref[b]] for b in BONES if ref[b] is not None}
    SB = ['IndexFinger1_L', 'RingFinger3_L', 'Thumb3_R', 'Thumb2_R', 'MiddleFinger2_R', 'LittleFinger3_R', 'Thumb3_L']
    R['raw'] = {b: [[round(r['t'], 2), r['stage'], [round(x, 4) for x in r['q'][b]], r.get('pitch')] for r in rec[::3] if r['stage'] in ('idle', 'look', 'walk')] for b in ('Thumb3_R', 'Thumb2_R', 'Thumb3_L')}
    R['series'] = {b: [[round(r['t'], 2), r['stage'], round(ang(r['q'][b], ref[b]), 1) if ref[b] else None] for r in rec[::3]] for b in SB}
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
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'; S['t'] = now
            return
        if st == 'settle' and now >= S['t']:
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(True); S['mesh'] = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); R['mesh_ok'] = S['mesh'] is not None; R['parents'] = {b: str(S['mesh'].get_parent_bone(b)) for b in ('Thumb3_R', 'Thumb2_R', 'Thumb3_L', 'Thumb0_R', 'IndexFinger1_R')}; S['yaw'] = pc.get_control_rotation().yaw; S['st'] = 'run'; S['si'] = 0; S['ts'] = now; S['t0'] = now; return
        if st == 'run':
            name, dur = STAGES[S['si']]; t = now - S['ts']
            yaw = S['yaw']; fwd = unreal.Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)
            if name == 'look': pc.set_control_rotation(unreal.Rotator(roll=0, pitch=25 * math.sin(t * 2.0), yaw=yaw + 40 * math.sin(t * 1.3)))
            elif name == 'walk': p.add_movement_input(fwd, 0.5, False); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            elif name == 'walkfast': p.add_movement_input(fwd, 1.0, False); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            elif name == 'jump':
                if t < 0.1: p.jump()
            elif name == 'fire':
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
                if t > 0.3 and S.get('nf', 0) < 4 and now - S.get('lf', -9) > 0.5: S['nf'] = S.get('nf', 0) + 1; S['lf'] = now; p.call_method('FurinaRifleShot')
            elif name == 'reload':
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
                if not S.get('rl'): S['rl'] = True; p.call_method('FurinaRequestReload')
            else: pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            mesh = S['mesh']
            S['rec'].append({'stage': name, 'pitch': round(pc.get_control_rotation().pitch, 1), 't': now - S['t0'], 'q': {b: qv(mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).rotation) for b in BONES}})
            if t >= dur:
                S['si'] += 1; S['ts'] = now
                if S['si'] >= len(STAGES): S['st'] = 'end'; S['t'] = now
            return
        if st == 'end' and now >= S['t']:
            if S['rec']: analyze()
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_TWITCH_PROBE armed', TAG)
