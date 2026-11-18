"""Lyra PIE(Play 전에 무장, 이후 손대지 않기): 폰이 생기고 10초 뒤 3인칭, 이어서 1인칭에서 손/어깨 위치를 소총 기준 좌표로 기록하고, 다시 3인칭으로 돌려 lyra_idle_view.py(좌/우/뒤 HighResShot) 실행.
소총 기준: X=왼쪽, Y=앞, Z=위. 권총손잡이 앞면 y≈-11.5(z -5.5), 뒷면 y≈-16.6. -> Data/lyra_grip_probe.json"""
import unreal, json, sys, time, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
OUT = D + r'\Data\lyra_grip_probe.json'
BONES = ['Right-wrist', 'IndexFinger1_R', 'MiddleFinger1_R', 'LittleFinger1_R', 'Thumb1_R', 'Right-arm', 'Right-elbow', 'Left-wrist', 'MiddleFinger1_L', 'Left-arm', 'Left-elbow', 'Left-shoulder', 'Right-shoulder', 'Spine', 'Chest', 'Neck']
R = {}; S = {'st': 0, 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def snap(p, tag):
    comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
    mesh = comps['FurinaMesh']; rifle = comps['FurinaRifle']; inv = rifle.get_world_transform().inverse(); row = {}
    for b in BONES:
        w = mesh.get_socket_location(b); l = inv.transform_location(w) if hasattr(inv, 'transform_location') else unreal.MathLibrary.inverse_transform_location(rifle.get_world_transform(), w)
        row[b] = [round(l.x, 2), round(l.y, 2), round(l.z, 2)]; row[b + '_w'] = [round(w.x, 1), round(w.y, 1), round(w.z, 1)]
    def dist(a, b): return round((mesh.get_socket_location(a) - mesh.get_socket_location(b)).length(), 2)
    row['L_arm_reach'] = dist('Left-arm', 'Left-wrist'); row['R_arm_reach'] = dist('Right-arm', 'Right-wrist')
    row['L_upper'] = dist('Left-arm', 'Left-elbow'); row['L_lower'] = dist('Left-elbow', 'Left-wrist')
    row['rel'] = str(rifle.get_editor_property('relative_location'))
    R[tag] = row; save()
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        if S['st'] == 0: p.get_editor_property('FurinaFPWanted').set_active(False); S['st'] = 1; S['t'] = now + 10
        elif S['st'] == 1 and now >= S['t']: snap(p, 'tp'); p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 2; S['t'] = now + 3
        elif S['st'] == 2 and now >= S['t']:
            snap(p, 'fp'); unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s\\Data\\grip_fp.png"' % D)
            S['st'] = 3; S['t'] = now + 2
        elif S['st'] == 3 and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(False); S['st'] = 4; S['t'] = now + 2
        elif S['st'] == 4 and now >= S['t']:
            unreal.unregister_slate_post_tick_callback(S['h']); old = sys.argv; sys.argv = ['x', 'keep']
            try: exec(compile(open(D + r'\Scripts\Unreal\lyra_idle_view.py', encoding='utf-8').read(), 'lyra_idle_view.py', 'exec'), {'__name__': '__main__'})
            finally: sys.argv = old
            R['idle_view'] = 'armed'; save()
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_GRIP_PROBE armed')
