"""Lyra 에디터(`py <파일> [태그]`, PIE 중지 상태): PIE 에서 폰이 서 있는 3인칭 상태로 액터/메시와 주요 뼈(Hips, Spine, Chest, Neck, 팔/손목)의 월드 변환(위치+쿼터니언)을 기록 (등 매기/홀스터 위치 계산용).
 -> Data/lyra_bone_probe_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_bone_probe_%s.json' % TAG
R = {'tag': TAG}; S = {'st': 'open', 't': 0}
BONES = ['Hips', 'Spine', 'Chest', 'Neck', 'Head', 'Left-clavicle', 'Right-clavicle', 'Left-arm', 'Left-elbow', 'Left-wrist', 'Right-arm', 'Right-elbow', 'Right-wrist', 'Left-thigh', 'Right-thigh']
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def tq(t): q = t.rotation; return [q.x, q.y, q.z, q.w]
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        if st not in ('ending', 'done') and p is None and st != 'wait': return
        if st == 'wait':
            if p is not None and comp(p, 'FurinaBolt') is not None: S['st'] = 'settle'; S['t'] = now + 8
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if st == 'settle' and now >= S['t']:
            mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); at = p.get_actor_transform(); R['actor'] = {'loc': [at.translation.x, at.translation.y, at.translation.z], 'q': tq(at)}
            R['mesh'] = {'loc': [mesh.get_world_transform().translation.x, mesh.get_world_transform().translation.y, mesh.get_world_transform().translation.z], 'q': tq(mesh.get_world_transform()), 'scale': [mesh.get_world_transform().scale3d.x, mesh.get_world_transform().scale3d.y, mesh.get_world_transform().scale3d.z]}
            R['bones'] = {}
            for b in BONES:
                try: t = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD); R['bones'][b] = {'loc': [t.translation.x, t.translation.y, t.translation.z], 'q': tq(t)}
                except Exception as e: R['bones'][b] = str(e)[:60]
            R['rifle_world'] = None
            rifle = comp(p, 'FurinaRifle'); t = rifle.get_world_transform(); R['rifle_world'] = {'loc': [t.translation.x, t.translation.y, t.translation.z], 'q': tq(t)}
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_BONE_PROBE armed', TAG)
