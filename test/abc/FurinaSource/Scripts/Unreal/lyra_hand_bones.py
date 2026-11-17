"""Lyra PIE 중 실행: FurinaMesh 의 왼손 관련 소켓/뼈 이름과 현재 총 기준 위치(손바닥 위치 추정용) -> Data/lyra_hand_bones.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hand_bones.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = [c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
    names = [str(n) for n in mesh.get_all_socket_names()]; R['n'] = len(names)
    R['left'] = [n for n in names if 'left' in n.lower() or n.lower().endswith('_l')][:80]
    R['hand_like'] = [n for n in names if any(k in n.lower() for k in ('wrist', 'hand', 'finger', 'thumb', 'index', 'middle', 'ring', 'pinky', 'palm'))][:80]
    rifle = [c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]; inv = rifle.get_world_transform().inverse()
    pos = {}
    for n in R['hand_like']:
        v = inv.transform_location(mesh.get_socket_location(n)); pos[n] = [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
    R['pos'] = pos
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HAND_BONES', R.get('n'), R.get('error', '')[-200:])
