"""Lyra 에디터(PIE 중이어도 됨): LyraHeroComponent 입력 관련 속성 + HeroData_Furina 의 입력 설정 + (PIE면) 현재 입력 매핑 -> Data/lyra_hero_inputs.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hero_inputs.json'
R = {}
try:
    cdo = unreal.get_default_object(unreal.LyraHeroComponent)
    R['hero_props'] = [n for n in dir(cdo) if not n.startswith('_') and any(k in n.lower() for k in ('input', 'mapping', 'camera', 'config'))]
    for n in R['hero_props']:
        try: R['val_' + n] = str(cdo.get_editor_property(n))[:300]
        except Exception as e: pass
    pd = unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina')
    R['pawn_data_props'] = {n: str(pd.get_editor_property(n))[:200] for n in ('pawn_class', 'input_config', 'tag_relationship_mapping', 'default_camera_mode', 'ability_sets') if hasattr(pd, 'get_editor_property')}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['bp_hero_cdo'] = None
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w:
        pc = unreal.GameplayStatics.get_player_controller(w, 0)
        lp = pc.get_local_player() if hasattr(pc, 'get_local_player') else None
        R['lp'] = str(lp)
        R['enh_lib'] = [n for n in dir(unreal) if 'EnhancedInput' in n][:20]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_INPUTS', R.get('error', 'ok')[-200:])
