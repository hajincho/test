"""Lyra 에디터(PIE 중이어도 됨): 푸리나 폰 BP 변수 중 사격 관련 이름과 현재 PIE 폰 값 -> Data/lyra_pawn_vars.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pawn_vars.json'
R = {}
try:
    gc = unreal.load_object(None, '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP.ThirdPersonCharacter_BP_C')
    cdo = unreal.get_default_object(gc)
    names = [n for n in dir(cdo) if any(k in n.lower() for k in ('ammo', 'reserve', 'fire', 'shot', 'reload', 'ads', 'shoulder', 'rest', 'mode'))]
    R['names'] = names
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    R['world'] = str(w)
    if w:
        p = unreal.GameplayStatics.get_player_pawn(w, 0); R['pawn'] = str(p); vals = {}
        for n in names:
            try:
                v = p.get_editor_property(n)
                if isinstance(v, (bool, int, float, str)): vals[n] = v
            except Exception as e: pass
        R['values'] = vals
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PAWN_VARS', R.get('error', 'ok')[-200:])
