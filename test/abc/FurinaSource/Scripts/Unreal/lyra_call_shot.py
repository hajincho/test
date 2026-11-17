"""Lyra PIE 중 실행: 푸리나 폰의 FurinaRifleShot 이벤트를 직접 호출해 잔탄이 줄어드는지 확인(입력 경로와 사격 로직 분리) -> Data/lyra_call_shot.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_call_shot.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    R['before'] = p.get_editor_property('FurinaAmmo'); p.call_method('FurinaRifleShot'); R['after'] = p.get_editor_property('FurinaAmmo')
    R['names'] = [n for n in ('FurinaFireTimer', 'FurinaAuto', 'FurinaReloading', 'FurinaFPWanted') if True]
    for n in ('FurinaReloading', 'FurinaFPWanted', 'FurinaADS', 'FurinaAiming', 'FurinaProne', 'FurinaCrouching'):
        try: R[n] = str(p.get_editor_property(n))[:80]
        except Exception as e: R[n] = 'n/a'
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CALL_SHOT', R)
