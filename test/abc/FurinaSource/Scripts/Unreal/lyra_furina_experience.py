"""LYRA 에디터(헤드리스): 푸리나 Experience를 Lyra가 스캔하는 /Game/System/Experiences 로 옮겨 만든다(이전 /Game/Furina/Lyra/B_Furina_Experience 는 삭제).
B_ShooterGame_Elimination 복제 + DefaultPawnData = /Game/Furina/Lyra/HeroData_Furina.  -> FurinaSource/Data/lyra_furina_experience.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_experience.json'
R = {}
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
try:
    old = '/Game/Furina/Lyra/B_Furina_Experience'
    if EAL.does_asset_exist(old): R['old_deleted'] = EAL.delete_asset(old)
    dst = '/Game/System/Experiences/B_Furina_Experience'
    if not EAL.does_asset_exist(dst): R['dup'] = EAL.duplicate_asset('/ShooterCore/Experiences/B_ShooterGame_Elimination', dst)
    bp = unreal.load_asset(dst); cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('default_pawn_data', unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina'))
    BEL.compile_blueprint(bp); R['saved'] = EAL.save_loaded_asset(bp, False)
    R['pawn_data'] = str(unreal.get_default_object(bp.generated_class()).get_editor_property('default_pawn_data'))
    R['listing'] = [str(x) for x in EAL.list_assets('/Game/System/Experiences', recursive=False)]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
print('LYRA_FURINA_EXPERIENCE done'); unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
