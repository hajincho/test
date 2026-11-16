"""Lyra PIE 중 직접 실행: 월드의 모든 폰(클래스, 컨트롤러, 위치, 팀 ID)과 플레이어 컨트롤러의 폰/뷰 타깃/PlayerState -> Data/lyra_pie_pawns.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pie_pawns.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); R['world'] = w.get_path_name()
    R['pawns'] = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn):
        c = p.get_controller(); l = p.get_actor_location()
        R['pawns'].append([p.get_name(), p.get_class().get_name(), c.get_class().get_name() if c else None, [round(l.x), round(l.y), round(l.z)], bool(p.is_player_controlled())])
    pcs = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.PlayerController)
    R['pcs'] = []
    for pc in pcs:
        vt = pc.get_view_target(); pw = pc.get_controlled_pawn() if hasattr(pc, 'get_controlled_pawn') else None
        R['pcs'].append([pc.get_name(), pc.get_class().get_name(), str(pw), vt.get_name() if vt else None, str(pc.player_state)])
    R['player_pawn0'] = str(unreal.GameplayStatics.get_player_pawn(w, 0)); R['player_ctrl0'] = str(unreal.GameplayStatics.get_player_controller(w, 0))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PIE_PAWNS', R.get('error', 'ok')[-200:])
