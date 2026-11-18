"""Lyra PIE(Play 전에 무장): 현재 맵/경험에서 푸리나 메커니즘이 살아있는지 점검. 폰이 생기고 10초 뒤: 맵, 경험(가능하면), 모든 폰의 클래스/PawnData/컨트롤러, 플레이어 폰의 체력,
 FurinaAmmo, 소총/탄창 컴포넌트, 활성 입력 매핑(푸리나 IMC 와 Lyra IMC 가 각각 켜져 있는지), 사격 이벤트(FurinaRifleShot) 호출 전후 잔탄. 위로 2초 뒤 FP/TP 전환 후 뷰 상태.
사용: py "<파일>" <태그> -> Data/lyra_stage_probe_<태그>.json"""
import unreal, json, sys, time, traceback
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'run'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_stage_probe_%s.json' % TAG
R = {'tag': TAG}; S = {'st': 0, 't': 0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if p is None: return
        now = time.time()
        if S['st'] == 0: S['st'] = 1; S['t'] = now + 10; R['map'] = w.get_name(); return
        if S['st'] == 1 and now >= S['t']:
            R['player'] = {'class': p.get_class().get_name(), 'name': p.get_name()}
            try:
                ext = p.get_component_by_class(unreal.LyraPawnExtensionComponent); pd = ext.get_pawn_data() if ext else None; R['player']['pawn_data'] = pd.get_path_name() if pd else None
            except Exception as e: R['player']['pawn_data_err'] = str(e)[:80]
            try: R['player']['ammo'] = p.get_editor_property('FurinaAmmo')
            except Exception as e: R['player']['ammo_err'] = str(e)[:80]
            try:
                hc = p.get_component_by_class(unreal.LyraHealthComponent); R['player']['health'] = [hc.get_health(), hc.get_max_health()] if hc else None
            except Exception as e: R['player']['health_err'] = str(e)[:80]
            names = [c.get_name() for c in p.get_components_by_class(unreal.SceneComponent)]; R['player']['has_rifle'] = 'FurinaRifle' in names; R['player']['has_mag'] = 'FurinaMag' in names
            R['pawns'] = [[x.get_name(), x.get_class().get_name(), bool(x.is_player_controlled())] for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn)][:20]
            try:
                lp = unreal.GameplayStatics.get_player_controller(w, 0).get_local_player(); sub = unreal.get_engine_subsystem(unreal.EnhancedInputLocalPlayerSubsystem) if False else lp.get_subsystem(unreal.EnhancedInputLocalPlayerSubsystem)
                R['imc'] = {}
                for nm, path in (('Furina_Default_IMC', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'), ('Furina_Stance', '/Game/Furina/Input/IMC_FurinaStance'), ('Lyra_IMC_Default', '/Game/Input/Mappings/IMC_Default'),
                                 ('Lyra_IMC_ShooterGame', '/ShooterCore/Input/Mappings/IMC_ShooterGame'), ('Lyra_IMC_ShooterGame_KBM', '/ShooterCore/Input/Mappings/IMC_ShooterGame_KBM'), ('Lyra_IMC_ADS_Speed', '/ShooterCore/Input/Mappings/IMC_ADS_Speed'), ('Lyra_IMC_InventoryTest', '/ShooterExplorer/Input/Mappings/IMC_InventoryTest')):
                    a = unreal.load_asset(path); R['imc'][nm] = bool(sub.has_mapping_context(a)) if a else 'missing'
            except Exception as e: R['imc_err'] = str(e)[:160]
            try:
                R['exp'] = str(unreal.GameplayStatics.get_game_state(w).get_component_by_class(unreal.LyraExperienceManagerComponent).get_current_experience_or_none().get_name())
            except Exception as e: R['exp_err'] = str(e)[:100]
            R['ammo_before'] = R['player'].get('ammo')
            try: p.call_method('FurinaRifleShot'); S['shot'] = True
            except Exception as e: R['shot_err'] = str(e)[:100]
            S['st'] = 2; S['t'] = now + 1.5; save()
        elif S['st'] == 2 and now >= S['t']:
            try: R['ammo_after'] = p.get_editor_property('FurinaAmmo')
            except Exception: pass
            R['done'] = True; save(); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_STAGE_PROBE armed', TAG)
