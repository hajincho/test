"""테스트용(Play 전에 실행해 무장, 그다음 Play): 임시 GE(/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller, 무한 지속 스텁)를 만들고,
PIE에서 큐브 표적에 AbilitySystemComponent를 붙인 뒤 BP_FurinaBullet을 그쪽으로 쏴 GE가 적용되는지(활성 이펙트 수) 확인 -> Data/bullet_hit_test.json
끝나면 스텁 GE는 삭제해야 한다(Lyra의 실제 GE와 충돌 방지): ue_bullet_hit_test_cleanup.py"""
import unreal, json, time, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_hit_test.json'
GE_PATH = '/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller'
R = {'log': []}
S = {'t0': time.time(), 'stage': 0}
try:
    if not unreal.EditorAssetLibrary.does_asset_exist(GE_PATH):
        ge = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(GE_PATH, unreal.GameplayEffect) if False else None
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.GameplayEffect)
        at = unreal.AssetToolsHelpers.get_asset_tools()
        ge = at.create_asset('GE_Damage_Basic_SetByCaller', '/Game/GameplayEffects/Damage', None, f); R['created_ge'] = bool(ge)
        gc = unreal.load_object(None, GE_PATH + '.GE_Damage_Basic_SetByCaller_C'); cdo = unreal.get_default_object(gc)
        cdo.set_editor_property('duration_policy', unreal.GameplayEffectDurationType.INFINITE)
        unreal.BlueprintEditorLibrary.compile_blueprint(ge); unreal.EditorAssetLibrary.save_loaded_asset(ge, False)
except Exception: R['error_setup'] = traceback.format_exc()
def spawn(w, cls, loc, rot):
    tf = unreal.Transform(loc, rot, unreal.Vector(1, 1, 1))
    a = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(w, cls, tf)
    return unreal.GameplayStatics.finish_spawning_actor(a, tf)
def save():
    json.dump(R, open(OUT, 'w'), indent=1, default=str)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        t = time.time() - S['t0']
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None: return
        if S['stage'] == 0:
            S['stage'] = 1; S['ts'] = t; S['fired'] = 0; S['last'] = -1
            loc = pawn.get_actor_location(); S['ascs'] = []
            dc = unreal.load_class(None, '/Game/Furina/QA/BP_FurinaTestDummy.BP_FurinaTestDummy_C')
            for a in unreal.GameplayStatics.get_all_actors_of_class(w, dc):
                asc = a.get_component_by_class(unreal.AbilitySystemComponent)
                if asc: S['ascs'].append(asc)
            R['asc_added'] = len(S['ascs'])
            S['gec'] = unreal.load_class(None, GE_PATH + '.GE_Damage_Basic_SetByCaller_C'); R['ge_class'] = str(S['gec'])
        elif S['stage'] == 1:
            pc = unreal.GameplayStatics.get_player_controller(w, 0)
            dums = [x.get_owner() for x in S['ascs']]
            if dums and S['fired'] == 0 and 'aimed' not in S:
                S['aimed'] = True; cam = pc.player_camera_manager.get_camera_location(); dl = dums[0].get_actor_location()
                pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, dl + unreal.Vector(0, 0, 0))); R['cam'] = str(cam); R['dummy'] = str(dl); S['t_aim'] = t
            if 'aimed' in S and t - S['t_aim'] > 0.5 and S['fired'] < 3 and t - S['last'] > 0.3:
                S['last'] = t; S['fired'] += 1; pawn.call_method('FurinaRifleShot')
            bc = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
            for b in unreal.GameplayStatics.get_all_actors_of_class(w, bc):
                l = b.get_actor_location(); R.setdefault('bullet_track', []).append([round(t, 2), round(l.x), round(l.y), round(l.z)])
            if S['fired'] >= 3 and t - S['last'] > 2.0:
                tot = 0; per = []
                for asc in S['ascs']:
                    try:
                        n = asc.get_gameplay_effect_count(S['gec'], None)
                        if n: per.append([asc.get_owner().get_actor_label(), n])
                        tot += n
                    except Exception as e: R['count_err'] = str(e)[:200]
                R['effect_total'] = tot; R['hit_actors'] = per[:10]; R['bullet_track'] = R.get('bullet_track', [])[-40:]
                R['ammo'] = pawn.get_editor_property('FurinaAmmo'); S['stage'] = 2; save(); print('BULLET_HIT_TEST', {k: v for k, v in R.items() if k != 'bullet_track'}); unreal.unregister_slate_post_tick_callback(S['h'])
        elif False:
            pass
        elif S['stage'] == 99:
            asc = S['asc']
            try: R['effect_count'] = asc.get_gameplay_effect_count(S['gec'], None) if asc else None
            except Exception as e: R['effect_count_err'] = str(e)[:200]
            try: R['bullet_alive'] = bool(S['b']) and S['b'].is_valid() if hasattr(S['b'], 'is_valid') else None
            except Exception: R['bullet_alive'] = False
            S['stage'] = 2; save(); print('BULLET_HIT_TEST', R); unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); save(); unreal.unregister_slate_post_tick_callback(S['h'])
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('BULLET_HIT_TEST armed')
