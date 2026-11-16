"""Lyra PIE 중 직접 실행: LyraHealthComponent / AbilitySystemComponent 가 달린 액터 목록(이름, 클래스, 체력, 위치) -> Data/lyra_pie_targets.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pie_targets.json'
R = {'health': [], 'asc_only': []}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0); pl = pawn.get_actor_location() if pawn else None
    R['player'] = str(pl)
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        h = a.get_component_by_class(unreal.LyraHealthComponent); asc = a.get_component_by_class(unreal.AbilitySystemComponent)
        l = a.get_actor_location(); dist = round((l - pl).length()) if pl else None
        if h: R['health'].append([a.get_name(), a.get_class().get_name(), round(h.get_health(), 1), round(h.get_max_health(), 1), dist, [round(l.x), round(l.y), round(l.z)]])
        elif asc: R['asc_only'].append([a.get_name(), a.get_class().get_name(), dist])
    R['health'].sort(key=lambda x: x[4] if x[4] is not None else 1e9)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PIE_TARGETS', len(R['health']), len(R['asc_only']), R.get('error', '')[-200:])
