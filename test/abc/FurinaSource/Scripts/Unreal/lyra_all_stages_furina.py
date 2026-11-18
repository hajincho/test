"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 모든 스테이지(Experience)에 푸리나 방식을 적용한다.
B_Furina_Experience 와 같은 방식(lyra_furina_hero_setup.py C): (1) DefaultPawnData -> /Game/Furina/Lyra/HeroData_Furina  (2) 액션 세트에서 무기용 StandardComponents / StandardHUD / SharedInput(Lyra 공용 입력, 키 중복의 원인) 제거.
 (사람 플레이어 폰은 이미 /Game/B_LyraGameMode 의 GetDefaultPawnClassForController 오버라이드가 푸리나로 만들고 있다. 이 스크립트는 그 폰이 쓰는 PawnData(능력/입력 설정)와 액션 세트를 스테이지마다 맞춘다.)
대상: B_ShooterGame_Elimination(Expanse), B_LyraShooterGame_ControlPoints(Convolution, ShooterGym), B_ShooterGame_Perf(ShooterPerf), B_TestInventoryExperience(Explorer 테스트 맵 3개),
      B_LyraDefaultExperience(L_DefaultEditorOverview), B_TopDownArenaExperience / B_TopDownArena_Multiplayer_Experience(Exploder 2종).  B_LyraFrontEnd_Experience(메뉴, 폰 없음)는 제외.
원래 값은 Data/lyra_all_stages_orig.json 에 처음 한 번 저장(되돌리려면 `py <파일> revert`).   -> Data/lyra_all_stages_furina.json"""
import unreal, json, os, sys, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_all_stages_furina.json'; ORIG = D_DIR + r'\lyra_all_stages_orig.json'
EXPS = ['/ShooterCore/Experiences/B_ShooterGame_Elimination', '/ShooterCore/Experiences/B_LyraShooterGame_ControlPoints', '/ShooterCore/Experiences/B_ShooterGame_Perf',
        '/ShooterExplorer/System/Experiences/B_TestInventoryExperience', '/Game/System/Experiences/B_LyraDefaultExperience',
        '/TopDownArena/System/Experiences/B_TopDownArenaExperience', '/TopDownArena/System/Experiences/B_TopDownArena_Multiplayer_Experience']
DROP = ('LAS_ShooterGame_StandardComponents', 'LAS_ShooterGame_StandardHUD', 'LAS_ShooterGame_SharedInput', 'LAS_InventoryTest')
REVERT = 'revert' in sys.argv
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
R = {'revert': REVERT, 'rows': {}}
try:
    furina = unreal.load_asset('/Game/Furina/Lyra/HeroData_Furina'); assert furina is not None
    orig = json.load(open(ORIG, encoding='utf-8')) if os.path.exists(ORIG) else {}
    for p in EXPS:
        row = {}; R['rows'][p] = row
        try:
            bp = unreal.load_asset(p + '.' + p.rsplit('/', 1)[1]) or unreal.load_asset(p); cdo = unreal.get_default_object(bp.generated_class())
            sets = list(cdo.get_editor_property('action_sets')); pawn = cdo.get_editor_property('default_pawn_data')
            if p not in orig:
                orig[p] = {'pawn': pawn.get_path_name() if pawn else None, 'sets': [x.get_path_name() for x in sets]}
                json.dump(orig, open(ORIG, 'w', encoding='utf-8'), indent=1)
            row['before'] = {'pawn': pawn.get_name() if pawn else None, 'sets': [x.get_name() for x in sets]}
            if REVERT:
                o = orig[p]; cdo.set_editor_property('default_pawn_data', unreal.load_asset(o['pawn']) if o['pawn'] else None)
                cdo.set_editor_property('action_sets', [unreal.load_asset(x) for x in o['sets']])
            else:
                cdo.set_editor_property('default_pawn_data', furina)
                cdo.set_editor_property('action_sets', [x for x in sets if x.get_name() not in DROP])
            BEL.compile_blueprint(bp); row['saved'] = bool(EAL.save_loaded_asset(bp, False))
            cdo = unreal.get_default_object(bp.generated_class()); row['after'] = {'pawn': cdo.get_editor_property('default_pawn_data').get_name(), 'sets': [x.get_name() for x in cdo.get_editor_property('action_sets')]}
        except Exception: row['error'] = traceback.format_exc()[-400:]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_ALL_STAGES', R.get('error', 'ok')[-200:])
