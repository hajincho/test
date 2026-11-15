"""PIE: stance recoil measurement. Requests a reload (FurinaRequestReload), waits 3.4 s, then fires <shots> (default 24) with FurinaRifleShot every 0.12 s and records the control-rotation pitch / yaw
change caused by every shot (recoil is added to the controller after the bullet spawns; the mouse is not moved). Also logs IsCrouching, FurinaProne flag and the FurinaProneWant variable.
-> Data/recoil_probe_<tag>.json (mean / std of the per-shot rise in degrees). usage: py ue_recoil_probe.py <tag> [shots]"""
import unreal, sys, json, time, math
TAG = sys.argv[1] if len(sys.argv) > 1 else 'x'
N = int(sys.argv[2]) if len(sys.argv) > 2 else 24
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\recoil_probe_%s.json' % TAG
S = {'t0': time.time(), 'req': False, 'rows': [], 'fired': 0, 'last': -1, 'before': None, 'state': None}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); ctl = unreal.GameplayStatics.get_player_controller(w, 0); t = time.time() - S['t0']
    if not S['req']: S['req'] = True; pc.call_method('FurinaRequestReload')
    rot = ctl.get_control_rotation()
    if S['before'] is not None:
        S['rows'].append(((rot.pitch - S['before'][0] + 180) % 360 - 180, (rot.yaw - S['before'][1] + 180) % 360 - 180)); S['before'] = None
    if t > 3.4 and t - S['last'] > 0.12 and S['fired'] < N:
        if S['state'] is None:
            S['state'] = dict(crouching=bool(pc.character_movement.is_crouching()), prone_flag=bool(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaProne')[0].is_active()), want=bool(pc.get_editor_property('FurinaProneWant')), ammo=pc.get_editor_property('FurinaAmmo'))
        S['last'] = t; S['fired'] += 1; S['before'] = (rot.pitch, rot.yaw); pc.call_method('FurinaRifleShot')
    del pc, ctl, w
    if S['fired'] >= N and t - S['last'] > 0.4:
        unreal.unregister_slate_post_tick_callback(S['h'])
        rows = [r for r in S['rows'] if abs(r[0]) < 5]
        p = [r[0] for r in rows]; y = [r[1] for r in rows]; n = max(1, len(p)); mp = sum(p) / n
        res = dict(tag=TAG, state=S['state'], shots=S['fired'], samples=len(p), mean_pitch_deg=round(mp, 4), std_pitch=round(math.sqrt(sum((a - mp) ** 2 for a in p) / n), 4), mean_abs_yaw=round(sum(abs(a) for a in y) / n, 4))
        json.dump(dict(summary=res, rows=S['rows']), open(OUT, 'w'), indent=1); print('RECOIL', res)
S['h'] = unreal.register_slate_post_tick_callback(tick)
