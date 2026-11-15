"""PIE: for <seconds> (default 7) logs every frame FurinaFireHold flag, the FireHold / ViewTP curves, Hips>Head lean and the rifle muzzle direction (mesh space, pitch deg: negative = down)
-> Data/fire_hold_probe.json. At t=1.0 s it calls FurinaRifleShot (as the fire timer does), at t=1.6 s it takes a HighResShot. Stand still in third person first. usage: py ue_fire_hold_probe.py [seconds]"""
import unreal, sys, json, time, math
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fire_hold_probe.json'
S = {'t0': time.time(), 'rows': [], 'shot': False, 'snap': False}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0); t = time.time() - S['t0']
    if t > 1.0 and not S['shot']: S['shot'] = True; pc.call_method('FurinaRifleShot')
    if t > 1.6 and not S['snap']: S['snap'] = True; unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2')
    comps = {c.get_name(): c for c in pc.get_components_by_class(unreal.SceneComponent)}
    m, r = comps['FurinaMesh'], comps['FurinaRifle']; ai = m.get_anim_instance(); T = m.get_world_transform(); RT = r.get_world_transform()
    def M(v): return unreal.MathLibrary.inverse_transform_location(T, v)
    o = M(RT.transform_location(unreal.Vector(0, 0, 0))); y = M(RT.transform_location(unreal.Vector(0, 1, 0))) - o
    hip, head = M(m.get_socket_location('Hips')), M(m.get_socket_location('Head'))
    S['rows'].append([round(t, 2), int(pc.get_components_by_tag(unreal.ActorComponent, 'FurinaFireHold')[0].is_active()), round(ai.get_curve_value('FireHold'), 2), round(ai.get_curve_value('ViewTP'), 2),
                      round(math.degrees(math.atan2(head.y - hip.y, head.z - hip.z)), 1), round(math.degrees(math.asin(max(-1, min(1, y.z / max(y.length(), 1e-6))))), 1), [round(x, 1) for x in o.to_tuple()]])
    del pc, comps, m, r, ai, w
    if t > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(dict(cols=['t', 'flag', 'FireHold', 'ViewTP', 'lean_hips_head', 'muzzle_pitch', 'rifle_origin'], rows=S['rows']), open(OUT, 'w')); print('FIRE_HOLD_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
