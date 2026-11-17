"""Lyra PIE(Play 전에 무장): 1인칭 강제 후 8000cm 위로 올려 떨어뜨리며 FPCamera 활성(=1인칭), 속도, 지면 여부를 0.3초마다 기록 -> Data/lyra_fall_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fall_probe.json'
R = {'samples': []}; S = {'st': 0, 't': 0, 'last': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        if S['st'] == 0: S['st'] = 1; S['t'] = now
        elif S['st'] == 1 and now - S['t'] > 12:
            p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 2; S['t'] = now
        elif S['st'] == 2 and now - S['t'] > 3:
            l = p.get_actor_location(); R['start'] = [l.x, l.y, l.z]; p.set_actor_location(unreal.Vector(l.x, l.y, l.z + 8000), False, False); S['st'] = 3; S['t'] = now; S['last'] = 0
        elif S['st'] == 3:
            if now - S['last'] > 0.3:
                S['last'] = now; v = p.get_velocity(); cm = p.get_editor_property('character_movement')
                R['samples'].append({'t': round(now - S['t'], 1), 'z': round(p.get_actor_location().z), 'vz': round(v.z), 'speed': round(v.length()), 'fp_active': bool(p.get_editor_property('FPCamera').is_active()),
                                     'falling': bool(cm.is_falling()), 'forced_flag_view': str(p.get_editor_property('FurinaFPWanted').is_active())}); save()
            if now - S['t'] > 14:
                R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FALL_PROBE armed')
