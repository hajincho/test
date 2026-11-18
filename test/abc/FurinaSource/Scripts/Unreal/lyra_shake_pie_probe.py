"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 오버뷰 맵에서 PIE 를 시작하고 폰이 생기면 10초 뒤: (1) 비조준 1발 (2) FurinaADS 활성 후 1발 (3) FurinaShoulder 활성 상태 1발 — 발사 직후 0.6초 동안 매 틱
(카메라 뷰 회전 - 컨트롤 회전) 차이를 기록(셰이크 크기). 끝나면 PIE 종료, 오버라이드/맵 복귀.   -> Data/lyra_shake_pie_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_shake_pie_probe.json'
R = {'cases': []}; S = {'st': 'open', 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(name):
    unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), name))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CASES = [('direct', None), ('direct_bundle', None), ('hip', None), ('ads', 'FurinaADS'), ('shoulder', 'FurinaShoulder')]
def comp(p, n):
    for c in p.get_components_by_class(unreal.ActorComponent):
        if c.get_name() == n: return c
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play' and now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90; return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None: S['st'] = 'settle'; S['t'] = now + 10
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            S['i'] = 0; S['st'] = 'prep'; return
        if st == 'prep':
            if S['i'] >= len(CASES): S['st'] = 'end'; return
            name, cn = CASES[S['i']]
            for c in ('FurinaADS', 'FurinaShoulder'):
                x = comp(p, c)
                if x: x.set_active(False)
            if cn: comp(p, cn).set_active(True)
            S['cur'] = {'case': name, 'ads': bool(comp(p, 'FurinaADS').is_active()), 'sh': bool(comp(p, 'FurinaShoulder').is_active()), 'diffs': []}
            S['st'] = 'prefire'; S['t'] = now + 1.5; return
        if st == 'prefire' and now >= S['t']:
            S['cur']['rot_before'] = str(pc.get_control_rotation()); S['cur']['ammo0'] = p.get_editor_property('FurinaAmmo'); (S['cur'].__setitem__('inst', (lambda r: [str(r), str(r.get_root_shake_pattern()) if r else None, str(pc.player_camera_manager.get_editor_property('camera_shake_cam_mod_class') if False else '')])(pc.player_camera_manager.start_camera_shake(unreal.load_class(None, ('/Game/3DPlatformerGameBundle/CameraShakes/Medium_Camera_Shake_BP.Medium_Camera_Shake_BP_C' if S['cur']['case'] == 'direct_bundle' else '/Game/Furina/CameraShakes/CS_FurinaShot.CS_FurinaShot_C')), 3.0))) if S['cur']['case'].startswith('direct') else p.call_method('FurinaRifleShot')); S['t0'] = now; S['st'] = 'sample'; return
        if st == 'sample':
            vrot = pc.player_camera_manager.get_camera_rotation(); crot = pc.get_control_rotation()
            def d(a, b):
                x = (a - b + 180.0) % 360.0 - 180.0; return round(x, 3)
            S['cur']['diffs'].append([round(now - S['t0'], 3), d(vrot.pitch, crot.pitch), d(vrot.yaw, crot.yaw), d(vrot.roll, crot.roll)])
            if now - S['t0'] > 0.7:
                S['cur']['ammo1'] = p.get_editor_property('FurinaAmmo'); dd = S['cur']['diffs']; S['cur']['max_abs'] = [max(abs(r[i]) for r in dd) for i in (1, 2, 3)]; R['cases'].append(S['cur']); save(); S['i'] += 1; S['st'] = 'prep'
            return
        if st == 'end':
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_SHAKE_PIE armed')
