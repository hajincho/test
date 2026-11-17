"""Lyra PIE 중 실행: 지금 화면을 HighResShot 3 배율로 저장(소총 탄창 부근 확인용)하고 FP 여부/탄약 기록 -> Data/lyra_snap.json. 스크린샷은 Saved/Screenshots/WindowsEditor/"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_snap.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    R['fp_active'] = bool(p.get_editor_property('FPCamera').is_active()); R['ammo'] = p.get_editor_property('FurinaAmmo')
    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 3'); R['shot'] = True; R['t'] = time.time()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_SNAP', R)
