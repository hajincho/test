"""Lyra 에디터(PIE 중지 상태에서 `py <파일>`): 에디터 월드 높은 곳(Z=5000)에 SK_M4A1 총몸 + SM_M4Mag 탄창을 인게임과 같은 상대 변환(회전 0, 이동 0)으로 세우고,
탄창 하부를 여러 각도에서 에디터 뷰포트 카메라로 찍어 Data/magview_<이름>.png 로 저장한다(끝나면 임시 액터 삭제, 레벨은 저장하지 않는다).
-> Data/lyra_mag_view.json"""
import unreal, json, time, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D + r'\lyra_mag_view.json'
BASE = unreal.Vector(0, 0, 5000)
T = unreal.Vector(0, -1.9, 5000 - 5.0)   # 탄창 하부(삽입구 아래) 근처
VIEWS = [('left', (34, 0, 0)), ('right', (-34, 0, 0)), ('front', (0, -34, 0)), ('back', (0, 34, 0)),
         ('below_left', (22, -14, -22)), ('below_right', (-22, -14, -22)), ('under', (0, -2, -34)), ('wide_left', (70, 0, 6))]
R = {'shots': []}; S = {'st': 0, 't': 0, 'i': 0, 'actors': []}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def cleanup():
    for a in S['actors']:
        try: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        except Exception: pass
    S['actors'] = []
def tick(dt):
    try:
        now = time.time()
        if S['st'] == 0:
            sk = unreal.load_asset('/Game/Furina/M4/SK_M4A1'); sm = unreal.load_asset('/Game/Furina/M4/SM_M4Mag')
            a = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.SkeletalMeshActor, BASE); a.skeletal_mesh_component.set_skeletal_mesh_asset(sk); S['actors'].append(a)
            b = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.StaticMeshActor, BASE); b.static_mesh_component.set_static_mesh(sm); S['actors'].append(b)
            for comp, nm in ((a.skeletal_mesh_component, 'rifle'), (b.static_mesh_component, 'mag')):
                R[nm + '_materials'] = [str(m.get_name()) if m else None for m in comp.get_materials()]
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).set_selected_level_actors([]); S['st'] = 1; S['t'] = now + 1.5
        elif S['st'] == 1 and now >= S['t']:
            name, off = VIEWS[S['i']]; loc = T + unreal.Vector(*off)
            unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, unreal.MathLibrary.find_look_at_rotation(loc, T)); S['st'] = 2; S['t'] = now + 1.5
        elif S['st'] == 2 and now >= S['t']:
            name = VIEWS[S['i']][0]
            unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1600x1000 filename="%s\\magview_%s.png"' % (D, name)); R['shots'].append(name); save()
            S['i'] += 1; S['st'] = 1; S['t'] = now + 2.0
            if S['i'] >= len(VIEWS): S['st'] = 3; S['t'] = now + 3.0
        elif S['st'] == 3 and now >= S['t']:
            cleanup(); R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); cleanup(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_MAG_VIEW armed')
