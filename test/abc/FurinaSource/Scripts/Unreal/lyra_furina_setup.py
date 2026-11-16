"""LYRA 에디터(헤드리스)에서 실행. 푸리나 콘텐츠를 Lyra에 맞춘다.
 1) 푸리나/플랫포머 블루프린트 전체 컴파일 점검 (상태 != UP_TO_DATE 인 것 기록)
 2) BP_FurinaBullet.FurinaDamageEffect = /Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller (피해량 FurinaDamage 는 0 유지)
 3) /Game/Furina/Lyra/HeroData_Furina (HeroData_ShooterGame 복제, PawnClass = ThirdPersonCharacter_BP)
 4) /Game/Furina/Lyra/B_Furina_Experience (B_ShooterGame_Elimination 복제, DefaultPawnData = HeroData_Furina)
 5) L_FiringRange_WP 월드 설정의 DefaultGameplayExperience = B_Furina_Experience (맵 저장)
실행: UnrealEditor.exe LyraStarterGame.uproject -ExecutePythonScript="<이 파일>" -nullrhi -unattended -nosplash -log   -> FurinaSource/Data/lyra_furina_setup.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_furina_setup.json'
R = {'step': []}
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/JumpPadCharacterBP/ThirdPersonCharacter_BP'
def step(name, fn):
    try: R['step'].append([name, fn()])
    except Exception: R['step'].append([name, 'ERROR ' + traceback.format_exc()[-600:]])
def compile_all():
    bad = {}; n = 0
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for root in ('/Game/Furina', '/Game/3DPlatformerGameBundle', '/Game/TFPMovement', '/Game/Free_Crawl_Animation'):
        for a in ar.get_assets_by_path(root, recursive=True):
            cn = str(a.asset_class_path.asset_name)
            if cn in ('Blueprint', 'WidgetBlueprint', 'AnimBlueprint'):
                obj = a.get_asset(); n += 1
                try: BEL.compile_blueprint(obj)
                except Exception as e: bad[str(a.package_name)] = 'compile err ' + str(e)[:80]; continue
                st = str(obj.get_editor_property('status')) if obj.get_editor_property('status') is not None else ''
                if 'UP_TO_DATE' not in st or 'WARNINGS' in st: bad[str(a.package_name)] = st
    R['bp_total'] = n; R['bp_not_clean'] = bad
    return n
def bullet():
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet'); cdo = unreal.get_default_object(bp.generated_class())
    ge = unreal.load_class(None, '/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller.GE_Damage_Basic_SetByCaller_C'); assert ge, 'GE class'
    cdo.set_editor_property('FurinaDamageEffect', ge); BEL.compile_blueprint(bp); ok = EAL.save_loaded_asset(bp, False)
    return [str(unreal.get_default_object(bp.generated_class()).get_editor_property('FurinaDamageEffect')), cdo.get_editor_property('FurinaDamage'), ok]
def pawn_data():
    dst = '/Game/Furina/Lyra/HeroData_Furina'
    if not EAL.does_asset_exist(dst): EAL.make_directory('/Game/Furina/Lyra'); assert EAL.duplicate_asset('/ShooterCore/Game/HeroData_ShooterGame', dst), 'dup pawn data'
    a = unreal.load_asset(dst); cls = unreal.load_class(None, PAWN + '.ThirdPersonCharacter_BP_C'); assert cls, 'pawn class'
    a.set_editor_property('pawn_class', cls); ok = EAL.save_loaded_asset(a, False)
    return [str(a.get_editor_property('pawn_class')), ok]
def experience():
    dst = '/Game/Furina/Lyra/B_Furina_Experience'
    if not EAL.does_asset_exist(dst): assert EAL.duplicate_asset('/ShooterCore/Experiences/B_ShooterGame_Elimination', dst), 'dup experience'
    bp = unreal.load_asset(dst); cdo = unreal.get_default_object(bp.generated_class())
    pd = unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina'); cdo.set_editor_property('default_pawn_data', pd)
    BEL.compile_blueprint(bp); ok = EAL.save_loaded_asset(bp, False)
    return [str(cdo.get_editor_property('default_pawn_data')), ok]
def world_settings():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); assert les.load_level('/ShooterMaps/Maps/L_FiringRange_WP'), 'load map'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); ws = w.get_world_settings()
    R['ws_class'] = ws.get_class().get_name(); R['ws_props'] = [p for p in dir(ws) if 'xperience' in p]
    cls = unreal.load_class(None, '/Game/Furina/Lyra/B_Furina_Experience.B_Furina_Experience_C')
    R['ws_before'] = str(ws.get_editor_property('default_gameplay_experience'))
    ws.set_editor_property('default_gameplay_experience', unreal.SoftClassPath('/Game/Furina/Lyra/B_Furina_Experience.B_Furina_Experience_C')) if hasattr(unreal, 'SoftClassPath') and False else ws.set_editor_property('default_gameplay_experience', cls)
    R['ws_after'] = str(ws.get_editor_property('default_gameplay_experience'))
    return les.save_current_level()
step('compile_all', compile_all); step('bullet', bullet); step('pawn_data', pawn_data); step('experience', experience); step('world_settings', world_settings)
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
print('LYRA_FURINA_SETUP done'); unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
