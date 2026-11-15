"""PIE probe for <seconds>: per frame MaxWalkSpeed, speed, flags, boom socket offset, follow FOV, control rotation, bullets alive
-> Data/fp_stance_probe.json. usage: py ue_fp_stance_probe.py [seconds]"""
import unreal, sys, json, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_stance_probe.json'
S = {'t0': time.time(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    pc = unreal.GameplayStatics.get_player_character(w, 0)
    def flag(t):
        c = pc.get_components_by_tag(unreal.ActorComponent, t); return bool(c and c[0].is_active())
    boom = pc.get_components_by_class(unreal.SpringArmComponent)[0]
    cams = {c.get_name(): c for c in pc.get_components_by_class(unreal.CameraComponent)}
    so = boom.get_editor_property('socket_offset'); r = pc.get_control_rotation()
    S['rows'].append([round(time.time() - S['t0'], 3), round(pc.character_movement.get_editor_property('max_walk_speed')), round(pc.get_velocity().length()),
                      flag('FurinaADS'), flag('FurinaShoulder'), flag('FurinaShoulderLeft'), flag('FurinaSpeedCap'),
                      round(so.y, 1), round(so.z, 1), round(cams['FollowCamera'].field_of_view, 1), round(r.pitch, 2), round(r.yaw, 2)])
    del pc, boom, cams, w
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(dict(cols=['t', 'mws', 'speed', 'ads', 'sh', 'left', 'cap', 'offY', 'offZ', 'fov', 'pitch', 'yaw'], rows=S['rows']), open(OUT, 'w'))
        print('STANCE_PROBE', len(S['rows']))
S['h'] = unreal.register_slate_post_tick_callback(tick)
