"""Lyra PIE 중 직접 실행: 컨트롤러 없는 푸리나 폰이 있으면 플레이어 컨트롤러로 possess 시도 -> Data/lyra_pie_possess.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pie_possess.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_controller(w, 0)
    free = [p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn) if p.get_controller() is None]
    R['free'] = [p.get_name() for p in free]
    if free:
        pc.possess(free[0]); R['after'] = str(unreal.GameplayStatics.get_player_pawn(w, 0)); R['controller_of_free'] = str(free[0].get_controller())
        R['auto_possess_player'] = str(free[0].get_editor_property('auto_possess_player')); R['auto_possess_ai'] = str(free[0].get_editor_property('auto_possess_ai'))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PIE_POSSESS', R)
