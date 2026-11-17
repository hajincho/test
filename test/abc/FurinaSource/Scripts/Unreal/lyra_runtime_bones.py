"""Lyra PIE 중 실행: FurinaMesh 런타임 뼈/소켓 이름 중 몸통/어깨 관련과 현재 폰 로컬 위치 -> Data/lyra_runtime_bones.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_runtime_bones.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    body = [c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
    inv = p.get_actor_transform().inverse()
    names = [str(n) for n in body.get_all_socket_names()]
    keys = ('spine', 'chest', 'neck', 'head', 'shoulder', 'clav', 'hips', 'pelvis', 'arm', 'breast', 'bust')
    pick = [n for n in names if any(k in n.lower() for k in keys) and 'HB' not in n and 'twist' not in n.lower()]
    R['names'] = pick[:60]
    R['pos'] = {}
    for n in pick[:60]:
        v = inv.transform_location(body.get_socket_location(n)); R['pos'][n] = [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_RUNTIME_BONES', R.get('error', 'ok')[-200:])
