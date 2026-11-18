"""Lyra PIE(Play 전에 무장, 이후 손대지 않기): 폰이 생기고 6초 뒤 3인칭으로 바꾸고, 소총 탄창 주변을 여러 각도(왼쪽/오른쪽/앞/뒤/아래-왼쪽)에서 보는 카메라 액터를 PIE 월드에 만들어 시점을 옮기며 HighResShot 을 Data/magcam_<이름>.png 로 저장.
소총 컴포넌트 축: X=좌우(탄창 삽입구 +-1.5), Y=앞뒤, Z=위아래(탄창은 -Z 방향).  -> Data/lyra_mag_cam.json"""
import unreal, json, time, traceback, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D + r'\lyra_mag_cam.json'
R = {'shots': []}; S = {'st': 0, 't': 0, 'i': 0, 'cam': None}
# (이름, 소총 로컬 오프셋(X,Y,Z), 거리 cm)  카메라는 탄창 중심을 바라봄
VIEWS = [('left', (1, 0, 0), 45), ('right', (-1, 0, 0), 45), ('front', (0, -1, 0), 45), ('back', (0, 1, 0), 45), ('below_left', (0.8, -0.3, -0.7), 45)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
        rifle = comps['FurinaRifle']; mag = comps['FurinaMag']
        if S['st'] == 0:
            p.get_editor_property('FurinaFPWanted').set_active(False); S['st'] = 1; S['t'] = now + 6
        elif S['st'] == 1 and now >= S['t']:
            cams = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor)  # PIE 월드엔 액터 생성 API 가 없어 기존 액터를 임시 카메라로 쓴다(저장되지 않음)
            cam = cams[0]; S['cam'] = cam; R['cam'] = str(cam.get_name())
            cam.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            S['st'] = 2; S['t'] = now
        elif S['st'] == 2 and now >= S['t']:
            name, off, dist = VIEWS[S['i']]
            rt = rifle.get_world_transform(); tgt = mag.get_world_location() + unreal.MathLibrary.transform_direction(rt, unreal.Vector(0, 0, 3))
            v = unreal.MathLibrary.transform_direction(rt, unreal.Vector(*off)); v = v / max(v.length(), 1e-6)
            loc = tgt + v * dist
            cam = S['cam']; cam.set_actor_location(loc, False, False)  # 액터 위치/회전이 곧 시점
            cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, tgt), False)
            pc = unreal.GameplayStatics.get_player_controller(w, 0); pc.set_view_target_with_blend(cam, 0.0)
            S['st'] = 3; S['t'] = now + 1.5
        elif S['st'] == 3 and now >= S['t']:
            name = VIEWS[S['i']][0]
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 2 filename="%s\\magcam_%s.png"' % (D, name)); R['shots'].append(name); save()
            S['i'] += 1
            if S['i'] >= len(VIEWS): R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h']); return
            S['st'] = 2; S['t'] = now + 1.0
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_MAG_CAM armed')
