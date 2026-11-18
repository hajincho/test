"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): 오버뷰 맵에서 PIE 시작 -> 권총(FurinaSwapMid)으로 교체 -> 1인칭(+아래 시선)과 3인칭에서 캡처하고
양손 뼈대와 권총 프레임 경계를 권총 프레임 기준 좌표(X왼쪽, Y앞, Z위 cm = 소총 컴포넌트 기준과 같음)로 기록.   끝나면 PIE 종료, 오버라이드/맵 복귀.
캡처: Data/pistol_grip_<태그>_fp.png (1인칭), _fp_down.png (1인칭, 아래 보기), _tp.png (3인칭 옆)   -> Data/lyra_pistol_grip_probe_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'
OUT = D + '/lyra_pistol_grip_probe_%s.json' % TAG
R = {'tag': TAG}; S = {'st': 'open', 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
BONES = ['Right-wrist', 'Left-wrist', 'Thumb0_R', 'Thumb1_R', 'Thumb2_R', 'Thumb3_R', 'IndexFinger1_R', 'IndexFinger3_R', 'MiddleFinger1_R', 'MiddleFinger3_R', 'RingFinger1_R', 'RingFinger3_R', 'LittleFinger1_R', 'LittleFinger3_R',
         'Thumb0_L', 'Thumb1_L', 'Thumb2_L', 'Thumb3_L', 'IndexFinger1_L', 'IndexFinger3_L', 'MiddleFinger1_L', 'MiddleFinger3_L', 'RingFinger1_L', 'RingFinger3_L', 'LittleFinger1_L', 'LittleFinger3_L']
def shot(w, name): unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s/pistol_grip_%s_%s.png"' % (D, TAG, name))
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play' and now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90; return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            p.call_method('FurinaSwapMid'); S['st'] = 'swapped'; S['t'] = now + 4; return
        if st == 'swapped' and now >= S['t']:
            R['pistol_on'] = bool(comp(p, 'FurinaPistolOn').is_active()); p.get_editor_property('FurinaFPWanted').set_active(True); S['st'] = 'fp'; S['t'] = now + 2; return
        if st == 'fp' and now >= S['t']:
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=rot.yaw)); S['st'] = 'fp_shot'; S['t'] = now + 1; return
        if st == 'fp_shot' and now >= S['t']:
            shot(w, 'fp'); S['st'] = 'fp_down'; S['t'] = now + 1.5; return
        if st == 'fp_down' and now >= S['t']:
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-35, yaw=rot.yaw)); S['st'] = 'fp_down_shot'; S['t'] = now + 1.5; return
        if st == 'fp_down_shot' and now >= S['t']:
            shot(w, 'fp_down')
            rifle = comp(p, 'FurinaRifle'); frame = comp(p, 'FurinaPistolFrame', unreal.StaticMeshComponent); slide = comp(p, 'FurinaPistolSlide', unreal.StaticMeshComponent); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent)
            inv = rifle.get_world_transform().inverse()
            def g(v): t = inv.transform_location(v); return [round(t.x, 2), round(t.y, 2), round(t.z, 2)]
            R['bones'] = {b: g(mesh.get_socket_location(b)) for b in BONES}
            for nm, c in (('frame', frame), ('slide', slide)):
                o, e, r = unreal.SystemLibrary.get_component_bounds(c); R[nm] = {'center': g(o), 'extent': [round(e.x, 2), round(e.y, 2), round(e.z, 2)], 'rel_loc': str(c.relative_location), 'rel_rot': str(c.relative_rotation), 'rel_scale': str(c.relative_scale3d)}
            R['rifle_world'] = str(rifle.get_world_transform())
            save(); S['st'] = 'tp'; S['t'] = now + 0.5; return
        if st == 'tp' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(False); S['st'] = 'tp_look'; S['t'] = now + 2; return
        if st == 'tp_look' and now >= S['t']:
            rot = pc.get_control_rotation(); pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-3, yaw=p.get_actor_rotation().yaw + 90)); S['st'] = 'tp_shot'; S['t'] = now + 1.5; return
        if st == 'tp_shot' and now >= S['t']:
            shot(w, 'tp'); S['st'] = 'end'; S['t'] = now + 1; return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_PISTOL_GRIP_PROBE armed', TAG)
