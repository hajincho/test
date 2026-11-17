"""Lyra PIE(Play 전에 무장): 재장전 중 매 틱(슬로모 0.15) 왼손 뼈대(손목/중지 뿌리/검지/엄지)와 탄창(FurinaMag 경계 중심, 장착 위치 기준)의 총 기준 좌표(X왼쪽,Y앞,Z위 cm)를 기록.
-> Data/lyra_reload_mag_probe.json : samples[ t, magstate, mag_center, mag_extent, {bone: pos} ], seated_ref(장착 상태 탄창 중심) """
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_reload_mag_probe.json'
R = {'samples': []}; S = {'st': 0, 'ts': 0, 'fired': 0, 'last': -9}
BONES = ['MiddleFinger1_L', 'MiddleFinger3_L', 'IndexFinger1_L', 'Thumb1_L', 'LittleFinger1_L']
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = unreal.GameplayStatics.get_time_seconds(w); rifle = comp(p, 'FurinaRifle'); mesh = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); mag = comp(p, 'FurinaMag', unreal.StaticMeshComponent)
        if rifle is None or mesh is None or mag is None: return   # 폰 컴포넌트가 아직 준비 안 됨
        inv = rifle.get_world_transform().inverse()
        def g(v): t = inv.transform_location(v); return [round(t.x, 2), round(t.y, 2), round(t.z, 2)]
        if S['st'] == 0: S['st'] = 1; S['ts'] = now
        elif S['st'] == 1 and now - S['ts'] > 5:
            o, e, r = unreal.SystemLibrary.get_component_bounds(mag); R['seated_rot'] = (lambda r: [round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)])(unreal.MathLibrary.make_relative_transform(mag.get_world_transform(), rifle.get_world_transform()).rotation.rotator())
            try: R['grip_bone'] = [str(x) for x in (rifle.get_socket_transform('Grip', unreal.RelativeTransformSpace.RTS_COMPONENT).rotation.rotator(), rifle.get_socket_transform('Grip', unreal.RelativeTransformSpace.RTS_COMPONENT).translation)]
            except Exception as e: R['grip_err'] = str(e)[:80]
            R['seated_ref'] = {'center': g(o), 'extent': [round(e.x, 1), round(e.y, 1), round(e.z, 1)], 'visible': mag.is_visible()}
            S['st'] = 2; S['ts'] = now; S['fired'] = 0
        elif S['st'] == 2:
            if S['fired'] < 6 and now - S['last'] > 0.25: S['last'] = now; S['fired'] += 1; p.call_method('FurinaRifleShot')
            if S['fired'] >= 6 and now - S['last'] > 1.0:
                unreal.GameplayStatics.set_global_time_dilation(w, 0.15); p.call_method('FurinaRequestReload'); S['st'] = 3; S['ts'] = now
        elif S['st'] == 3:
            t = now - S['ts']; o, e, r = unreal.SystemLibrary.get_component_bounds(mag)
            row = {'t': round(t, 3), 'ms': round(mesh.get_anim_instance().get_curve_value('MagState'), 2), 'mag_vis': mag.is_visible(), 'mag_center': g(o), 'mag_ext': [round(e.x, 1), round(e.y, 1), round(e.z, 1)], 'wrist': g(mesh.get_socket_location('Left-wrist')), 'mag_rot': (lambda r: [round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)])(unreal.MathLibrary.make_relative_transform(mag.get_world_transform(), rifle.get_world_transform()).rotation.rotator())}
            for b in BONES:
                try: row[b] = g(mesh.get_socket_location(b))
                except Exception: pass
            R['samples'].append(row)
            if t > 3.4:
                unreal.GameplayStatics.set_global_time_dilation(w, 1.0); R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_RELOAD_MAG_PROBE armed')
