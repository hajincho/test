"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 스테이지별로 (맵 열기 -> 그 스테이지의 실제 경험으로 PIE -> 푸리나 점검 -> PIE 종료)를 자동으로 반복. 손대지 않는다.
각 항목: 맵 경로, 경험 이름. 점검: 플레이어 폰 클래스, 체력, FurinaAmmo, 소총/탄창 컴포넌트, 사격 이벤트 호출 전후 잔탄, 모든 폰, 이동(속도 입력은 못 넣으므로 생략), PIE 로그 오류 개수는 따로.
끝나면 경험 오버라이드를 B_Furina_Experience 로 되돌리고 시작 맵(L_DefaultEditorOverview)을 다시 연다.   -> Data/lyra_stage_sweep.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_stage_sweep.json'
STAGES = [('/Game/System/DefaultEditorMap/L_DefaultEditorOverview', 'B_LyraDefaultExperience'),
          ('/ShooterCore/Maps/L_ShooterGym', 'B_LyraShooterGame_ControlPoints'),
          ('/ShooterCore/Maps/L_ShooterPerf', 'B_ShooterGame_Perf'),
          ('/ShooterMaps/Maps/L_Convolution_Blockout', 'B_LyraShooterGame_ControlPoints'),
          ('/ShooterMaps/Maps/L_Expanse_Blockout', 'B_ShooterGame_Elimination'),
          ('/ShooterExplorer/Maps/L_InventoryTestMap', 'B_TestInventoryExperience'),
          ('/TopDownArena/Maps/L_TopDownArenaGym', 'B_TopDownArenaExperience'),
          ('/TopDownArena/Maps/L_TopDown_LocalMultiplayer', 'B_TopDownArena_Multiplayer_Experience')]
R = {'stages': []}; S = {'i': 0, 'st': 'open', 't': 0, 'cur': None}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(name):
    cdo = unreal.get_default_object(unreal.LyraDeveloperSettings); cdo.set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), name))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if S['i'] >= len(STAGES):
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); R['done'] = True; save(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h']); return
        mp, exp = STAGES[S['i']]
        if st == 'open':
            S['cur'] = {'map': mp, 'exp': exp}; setexp(exp)
            S['cur']['loaded'] = bool(unreal.EditorLoadingAndSavingUtils.load_map(mp)); S['st'] = 'play_req'; S['t'] = now + 4
        elif st == 'play_req' and now >= S['t']:
            LES().editor_request_begin_play(); S['st'] = 'wait_pawn'; S['t'] = now + 90   # 맵 로드/셰이더가 느릴 수 있어 90초까지 기다림
        elif st == 'wait_pawn':
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
            if p is not None: S['p_seen'] = now; S['st'] = 'settle'; S['t'] = now + 10
            elif now >= S['t']: S['cur']['error'] = 'no player pawn within 90 s'; S['st'] = 'end_req'
        elif st == 'settle' and now >= S['t']:
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0); c = S['cur']
            c['player'] = {'class': p.get_class().get_name()}
            try: c['player']['ammo'] = p.get_editor_property('FurinaAmmo')
            except Exception as e: c['player']['ammo_err'] = str(e)[:60]
            try: hc = p.get_component_by_class(unreal.LyraHealthComponent); c['player']['health'] = [hc.get_health(), hc.get_max_health()] if hc else None
            except Exception as e: c['player']['health_err'] = str(e)[:60]
            names = [x.get_name() for x in p.get_components_by_class(unreal.SceneComponent)]; c['player']['has_rifle'] = 'FurinaRifle' in names; c['player']['has_mag'] = 'FurinaMag' in names
            c['pawns'] = [[x.get_class().get_name(), bool(x.is_player_controlled())] for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn)][:12]
            c['ammo_before'] = c['player'].get('ammo')
            try: p.call_method('FurinaRifleShot')
            except Exception as e: c['shot_err'] = str(e)[:60]
            S['st'] = 'after_shot'; S['t'] = now + 1.5
        elif st == 'after_shot' and now >= S['t']:
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
            try: S['cur']['ammo_after'] = p.get_editor_property('FurinaAmmo')
            except Exception: pass
            S['st'] = 'end_req'
        elif st == 'end_req':
            R['stages'].append(S['cur']); save(); LES().editor_request_end_play(); S['st'] = 'ended'; S['t'] = now + 5
        elif st == 'ended' and now >= S['t']:
            S['i'] += 1; S['st'] = 'open'
    except Exception:
        R['error'] = traceback.format_exc(); R['at'] = [S['i'], S['st']]; save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_STAGE_SWEEP armed', len(STAGES))
