"""Lyra PIE(Play 전에 무장): 1인칭으로 바꾸고 5초 뒤부터 0.25초마다 8초간 양 팔꿈치/손목 위치를 소총 기준으로 기록(팔꿈치만 흔들리고 손은 고정인지) -> Data/lyra_sway_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_sway_probe.json'
R = {'samples': []}; S = {'st': 0, 't': 0, 'last': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time(); comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
        mesh = comps['FurinaMesh']; rifle = comps['FurinaRifle']
        if S['st'] == 0: p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 1; S['t'] = now + 5
        elif S['st'] == 1 and now >= S['t']:
            if now - S['last'] >= 0.25:
                S['last'] = now; row = {'t': round(now - S['t'], 2)}
                for b in ('Right-elbow', 'Left-elbow', 'Right-wrist', 'Left-wrist'):
                    l = unreal.MathLibrary.inverse_transform_location(rifle.get_world_transform(), mesh.get_socket_location(b)); row[b] = [round(l.x, 2), round(l.y, 2), round(l.z, 2)]
                R['samples'].append(row)
            if now - S['t'] > 8: R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_SWAY_PROBE armed')
