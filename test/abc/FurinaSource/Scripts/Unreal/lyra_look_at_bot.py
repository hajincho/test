"""Lyra PIE 중 실행: 플레이어를 첫 봇 앞 350cm 에 세우고 봇을 바라보게 한다(눈으로 봇 애니메이션 확인용). -> Data/lyra_look_at_bot.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_look_at_bot.json'
R = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    me = unreal.GameplayStatics.get_player_pawn(w, 0)
    bots = [p for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if 'Mannequin' in p.get_class().get_name()]
    b = bots[0]; bl = b.get_actor_location(); R['bot'] = [b.get_name(), [round(bl.x), round(bl.y), round(bl.z)]]
    d = unreal.Vector(350, 0, 0); pos = unreal.Vector(bl.x - 350, bl.y, bl.z)
    me.set_actor_location(pos, False, False)
    pc = unreal.GameplayStatics.get_player_controller(w, 0); pc.set_control_rotation(unreal.Rotator(0, 0, 0))
    R['ok'] = True
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LOOK_BOT', R)
