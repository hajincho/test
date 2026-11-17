"""Lyra PIE 중 실행: 지금 자세에서 소총 컴포넌트(FurinaRifle) 대비 'Grip' 뼈대 변환(몸통 메시가 따라가는 값)과 탄창(FurinaMag)/FurinaMagRef 컴포넌트 변환 -> Data/lyra_mag_rest_probe.json
몸통은 Grip 뼈대에 100% 스키닝돼 있으므로 Grip 뼈대가 컴포넌트에서 회전/이동해 있으면, 컴포넌트에 붙은 탄창과 어긋난다."""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_mag_rest_probe.json'
R = {}
def rot(r): return [round(r.roll, 2), round(r.pitch, 2), round(r.yaw, 2)]
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    comps = {c.get_name(): c for c in p.get_components_by_class(unreal.SceneComponent)}
    rifle = comps['FurinaRifle']; mag = comps['FurinaMag']
    R['bones'] = [str(rifle.get_bone_name(i)) for i in range(rifle.get_num_bones())]
    R['sockets'] = [str(n) for n in rifle.get_all_socket_names()][:40]
    for b in R['bones'][:12]:
        t = rifle.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_COMPONENT); R['bone_' + b] = {'rot': rot(t.rotation.rotator()), 'loc': [round(t.translation.x, 2), round(t.translation.y, 2), round(t.translation.z, 2)], 'scale': [round(t.scale3d.x, 3), round(t.scale3d.y, 3), round(t.scale3d.z, 3)]}
    rel = unreal.MathLibrary.make_relative_transform(mag.get_world_transform(), rifle.get_world_transform()); R['mag_rel'] = {'rot': rot(rel.rotation.rotator()), 'loc': [round(rel.translation.x, 2), round(rel.translation.y, 2), round(rel.translation.z, 2)]}
    R['mag_attach'] = [str(mag.get_attach_parent().get_name()) if mag.get_attach_parent() else None, str(mag.get_attach_socket_name())]
    R['rifle_attach'] = [str(rifle.get_attach_parent().get_name()) if rifle.get_attach_parent() else None, str(rifle.get_attach_socket_name())]
    ai = rifle.get_anim_instance(); R['rifle_anim_instance'] = ai.get_class().get_name() if ai else None
    R['anim_mode'] = str(rifle.get_editor_property('animation_mode'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAG_REST', R.get('error', 'ok')[-200:])
