"""Lyra PIE 중 실행: 3인칭 카메라 대신 Furina 메시(총과 손이 붙어 있음)를 폰 기준 yaw 로 돌려 옆/뒤에서 보이게 한다(스크린샷용).
py "<파일>" <yaw도>   예: 90 / -90 / 0(원복). 메시의 원래 상대 yaw 는 처음 실행 때 Data/lyra_side_view.json 의 base_yaw 에 저장하고 거기에 더한다."""
import unreal, sys, json, os, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_side_view.json'
R = {}
try:
    add = float(sys.argv[-1]); w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    m = [c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'CharacterMesh0'][0]
    rot = m.get_editor_property('relative_rotation'); R['now'] = [rot.roll, rot.pitch, rot.yaw]
    base = -90.0   # Lyra/템플릿 메시 기본 상대 yaw
    m.set_editor_property('relative_rotation', unreal.Rotator(roll=rot.roll, pitch=rot.pitch, yaw=base + add)); R['set_yaw'] = base + add
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w'), indent=1, default=str); print('LYRA_SIDE_VIEW', R)
