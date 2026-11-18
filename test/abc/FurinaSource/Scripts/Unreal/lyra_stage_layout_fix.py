"""Lyra 에디터(`py <파일> [revert]`, PIE 중지 상태): 메인 화면 포탈로 스테이지에 들어오면 마우스로 시점이 안 돌아가는 문제 수정.
원인 추정: 포탈이 메뉴 레이어에 스피너(입력 일시 중지)를 띄우고, 무기용 HUD 세트(LAS_ShooterGame_StandardHUD)를 뺀 경험은 HUD 레이아웃(게임 입력 모드 설정)을 푸시하지 않아 UI 입력 모드가 남는다.
수정: StandardHUD 의 AddWidgets 레이아웃 요청(위젯 요소 없이 레이아웃만)을 레이아웃이 비어 있는 경험들의 AddWidgets 액션에 복사한다. 되돌리기: `revert` (레이아웃을 비움).
대상: B_Furina_Experience, B_ShooterGame_Elimination, B_LyraShooterGame_ControlPoints, B_ShooterGame_Perf, B_TestInventoryExperience.  -> Data/lyra_stage_layout_fix.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_stage_layout_fix.json'
EXPS = ['/Game/System/Experiences/B_Furina_Experience', '/ShooterCore/Experiences/B_ShooterGame_Elimination', '/ShooterCore/Experiences/B_LyraShooterGame_ControlPoints',
        '/ShooterCore/Experiences/B_ShooterGame_Perf', '/ShooterExplorer/System/Experiences/B_TestInventoryExperience']
REVERT = 'revert' in sys.argv
R = {'revert': REVERT, 'rows': {}}
try:
    hud = unreal.load_asset('/ShooterCore/Experiences/LAS_ShooterGame_StandardHUD')
    src = [a for a in hud.get_editor_property('actions') if a and 'AddWidgets' in a.get_class().get_name()][0]
    reqs = list(src.get_editor_property('layout')); R['src_layout'] = [x.export_text() for x in reqs]
    for p in EXPS:
        row = {}; R['rows'][p] = row
        try:
            bp = unreal.load_asset(p + '.' + p.rsplit('/', 1)[1]); cdo = unreal.get_default_object(bp.generated_class())
            acts = [a for a in cdo.get_editor_property('actions') if a and 'AddWidgets' in a.get_class().get_name()]
            row['n_actions'] = len(acts)
            a = acts[0]; row['before'] = [x.export_text() for x in a.get_editor_property('layout')]
            a.set_editor_property('layout', [] if REVERT else [r.copy() for r in reqs])
            row['after'] = [x.export_text() for x in a.get_editor_property('layout')]
            row['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(bp))
        except Exception: row['error'] = traceback.format_exc()[-400:]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_LAYOUT_FIX', REVERT)
