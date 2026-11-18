"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 경험 2개(B_Furina_Experience, B_ShooterGame_Elimination)로 차례로 PIE를 돌려 폰 생성 12초 뒤
활성 입력 매핑 컨텍스트(IMC)와 컨트롤러/폰 입력 관련 상태를 기록한다. (스테이지에서 마우스 시점 전환이 안 되는 원인 조사용)  끝나면 오버라이드를 B_Furina_Experience 로 되돌린다.  -> Data/lyra_imc_state_probe.json"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_imc_state_probe.json'
RUNS = [('/Game/System/DefaultEditorMap/L_DefaultEditorOverview', 'B_Furina_Experience'), ('/ShooterMaps/Maps/L_Expanse_Blockout', 'B_ShooterGame_Elimination')]
R = {'runs': []}; S = {'i': 0, 'st': 'open', 't': 0, 'cur': None}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(name):
    cdo = unreal.get_default_object(unreal.LyraDeveloperSettings); cdo.set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), name))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def probe(w, c):
    pc = unreal.GameplayStatics.get_player_controller(w, 0); p = unreal.GameplayStatics.get_player_pawn(w, 0)
    c['pc'] = pc.get_class().get_name(); c['pawn'] = p.get_class().get_name()
    try: c['ctrl_rot'] = str(pc.get_control_rotation())
    except Exception as e: c['rot_err'] = str(e)[:80]
    for k in ('input_yaw_scale', 'input_pitch_scale', 'ignore_look_input', 'ignore_move_input'):
        try: c[k] = str(pc.get_editor_property(k))
        except Exception as e: c[k + '_err'] = str(e)[:60]
    try: c['look_ignored'] = pc.is_look_input_ignored(); c['move_ignored'] = pc.is_move_input_ignored()
    except Exception as e: c['ign_err'] = str(e)[:80]
    c['pc_attrs'] = [n for n in dir(pc) if any(k in n.lower() for k in ('player', 'input_comp', 'local'))][:30]
    sub = None
    try:
        lp = pc.get_editor_property('player'); c['lp'] = str(lp)
        for fn in (lambda: unreal.EnhancedInputLibrary.get_enhanced_input_local_player_subsystem(pc), lambda: lp.get_subsystem(unreal.EnhancedInputLocalPlayerSubsystem), lambda: unreal.LocalPlayerSubsystem):
            try: sub = fn(); break
            except Exception as e: c.setdefault('sub_errs', []).append(str(e)[:80])
    except Exception as e: c['lp_err'] = str(e)[:100]
    c['sub'] = str(sub)
    if sub is not None:
        c['sub_attrs'] = [n for n in dir(sub) if 'mapping' in n.lower() or 'context' in n.lower()]
        ar = unreal.AssetRegistryHelpers.get_asset_registry(); c['imc'] = {}
        for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/EnhancedInput', 'InputMappingContext'), True):
            try:
                if sub.has_mapping_context(a.get_asset()): c['imc'][str(a.get_editor_property('package_name'))] = True
            except Exception as e: c['imc_err'] = str(e)[:80]; break
    try: c['loc'] = str(p.get_actor_location())
    except Exception: pass
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if S['i'] >= len(RUNS):
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); R['done'] = True; save(); S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h']); return
        mp, exp = RUNS[S['i']]
        if st == 'open':
            S['cur'] = {'map': mp, 'exp': exp}; setexp(exp); unreal.EditorLoadingAndSavingUtils.load_map(mp); S['st'] = 'play_req'; S['t'] = now + 4
        elif st == 'play_req' and now >= S['t']:
            LES().editor_request_begin_play(); S['st'] = 'wait_pawn'; S['t'] = now + 90
        elif st == 'wait_pawn':
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
            if p is not None: S['st'] = 'settle'; S['t'] = now + 12
            elif now >= S['t']: S['cur']['error'] = 'no pawn'; S['st'] = 'end_req'
        elif st == 'settle' and now >= S['t']:
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); probe(w, S['cur']); S['st'] = 'end_req'
        elif st == 'end_req':
            R['runs'].append(S['cur']); save(); LES().editor_request_end_play(); S['st'] = 'ended'; S['t'] = now + 5
        elif st == 'ended' and now >= S['t']:
            S['i'] += 1; S['st'] = 'open'
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_IMC_STATE armed')
