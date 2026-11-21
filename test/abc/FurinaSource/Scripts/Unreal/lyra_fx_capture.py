"""(lyra_fx_capture.py: 사격 효과·권총 3자세·조준경 확인용 변형, 2026-11-21) Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1 백그라운드): 지금 반영된 1인칭 무기 11종을 한 번의 PIE 에서 차례로 캡처(2026-11-21).
 무기마다: 대기(허리) -> 사격 직후 -> 재장전 중(시작 1.2초 뒤) -> 정조준. 재장전이 끝날 때까지 기다린 뒤 다음 무기로.
 캡처: Data/fpvm_all_<키>_<단계>.png   기록: Data/lyra_fpvm_capture_all.json("done": true)"""
import unreal, json, sys, time, traceback
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_fx_capture.json'
KEYS = ['p38', 'p08', 'pp', 'kar98k', 'kar98k_zf39', 'kar98k_zf41', 'g43', 'g43_zf4', 'mp40', 'mp38', 'stg44']
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'all'
if TAG == 'smoketest': KEYS = ['kar98k']
elif TAG == 'zf41': KEYS = ['kar98k_zf41']
elif TAG == 'mp40rl': KEYS = ['mp40', 'mp38']
elif TAG == 'case': KEYS = ['p38', 'p08', 'pp']
elif TAG == 'psh':   # 권총 견착(팔 뻗기) 확인
    STEPS = [('hip', 'key', 2.5), ('sh', 'sh_on', 1.2), ('sh_fire', 'fire', 0.03), ('sh_off', 'sh_off', 1.2)]; PISTOL_ONLY = ()
if TAG == 'caseslow': KEYS = ['p38', 'p08', 'pp']
elif TAG == 'psh': KEYS = ['p38', 'p08', 'pp']
elif TAG == 'v3': KEYS = ['kar98k_zf39', 'kar98k_zf41', 'g43_zf4', 'p38', 'p08', 'pp']
elif TAG == 'stance': KEYS = ['kar98k', 'g43', 'g43_zf4', 'mp40', 'mp38', 'stg44', 'p38']
elif TAG != 'all': KEYS = [k for k in KEYS if k in TAG.split('+')]   # 일부만 다시: 태그 'kar98k+kar98k_zf41'(ExecCmds 는 쉼표로 명령을 나눔)
BOLT = 1.3   # 볼트액션은 사격 뒤 볼트 조작(1.2초)이 끝나야 재장전이 받아짐
R = {'shots': [], 'events': []}; S = {'st': 'open', 't': 0, 'k': 0, 'i': 0, 'sub': 0}
# (이름, 동작, 대기초) — 대기는 동작 뒤 캡처까지
if TAG == 'smoketest': STEPS0 = [('hip', 'key', 2.0), ('st0', 'smoketest', 0.05), ('st1', None, 0.5), ('st2', 'smokeinfo', 1.5)]
STEPS = [('hip', 'key', 2.5), ('fire', 'fire', 0.0), ('smoke0', None, 0.0), ('smoke', None, 0.35), ('bolt_wait', None, 1.0),
         ('sh', 'sh_on', 0.9), ('sh_fire', 'fire', 0.0), ('sh_off', 'sh_off', 1.2),
         ('ads', 'ads_on', 1.3), ('ads_fire', 'fire', 0.0), ('ads_smoke', None, 0.35), ('ads_off', 'aim_off', 1.4)]
PISTOL_ONLY = ('sh', 'sh_fire', 'sh_off')
if TAG == 'caseslow':   # 0.1배속으로 탄피 확인
    STEPS = [('hip', 'key', 2.5), ('slow', 'slomo', 0.3), ('fire', 'fire', 0.3), ('s1', None, 0.3), ('s2', None, 0.3), ('s3', None, 0.6), ('ads', 'ads_on', 6.0), ('afire', 'fire', 0.3), ('as1', None, 0.3), ('as2', None, 0.3), ('as3', None, 0.6), ('ads_off', 'aim_off', 4.0), ('fast', 'slomo1', 0.5)]; PISTOL_ONLY = ()
if TAG == 'case':
    STEPS = [('hip', 'key', 2.5), ('fire', 'fire', 0.03), ('c1', None, 0.0), ('c2', None, 0.0), ('c3', None, 0.2), ('ads', 'ads_on', 1.3), ('afire', 'fire', 0.03), ('ac1', None, 0.0), ('ac2', None, 0.0), ('ads_off', 'aim_off', 0.8)]; PISTOL_ONLY = ()
if TAG == 'mp40rl':
    STEPS = [('hip', 'key', 2.5), ('rl1', 'reload', 0.3), ('rl2', None, 0.15), ('rl3', None, 0.3), ('rl4', None, 0.2), ('rl5', None, 0.2), ('rl_wait', 'wait_reload', 0.6)]; PISTOL_ONLY = ()
if TAG == 'zf41':
    STEPS = [('hip', 'key', 2.5), ('ads', 'ads_on', 1.5), ('ads_off', 'aim_off', 0.8)]; PISTOL_ONLY = ()
if TAG == 'v3':   # 조준경 화면 속 화면·권총 탄창 재장전·연기 끔 확인(2026-11-21)
    STEPS = [('hip', 'key', 2.5), ('fire', 'fire', 0.0), ('smoke', None, 0.4), ('bolt_wait', None, 1.0), ('ads', 'ads_on', 1.4), ('ads_off', 'aim_off', 1.0),
             ('rl1', 'reload', 0.45), ('rl2', None, 0.3), ('rl3', None, 0.35), ('rl4', None, 0.3), ('rl5', None, 0.3), ('rl_wait', 'wait_reload', 0.6)]
    PISTOL_ONLY = ()
if TAG == 'stance':   # 견착·재장전 구도 확인(2026-11-21)
    STEPS = [('hip', 'key', 2.5), ('sh', 'sh_on', 1.0), ('sh_off', 'sh_off', 0.8), ('ads', 'ads_on', 1.3), ('ads_off', 'aim_off', 1.0),
             ('rl1', 'reload', 0.7), ('rl2', None, 0.35), ('rl3', None, 0.35), ('rl4', None, 0.5), ('rl_wait', 'wait_reload', 0.6)]
    PISTOL_ONLY = ()
if TAG == 'smoketest': STEPS = STEPS0
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.ActorComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def status(p):
    vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent)
    an = p.get_editor_property('FurinaVMAnimIdle')
    return {'stance': p.get_editor_property('FurinaPStance'), 'idle_anim': an.get_name() if an else None, 'tube_hidden': p.get_editor_property('FurinaScopeTubeHidden'),
            'last_key': str(p.get_editor_property('FurinaVMLastKey')), 'n_panims': len(p.get_editor_property('FurinaPAnims')), 'ammo': p.get_editor_property('FurinaAmmo'), 'wid': str(p.get_editor_property('FurinaGameWeaponId')), 'rl': bool(p.get_editor_property('FurinaReloading')),
            'mesh': (vm.get_skeletal_mesh_asset().get_name() if vm and vm.get_skeletal_mesh_asset() else None), 'vm_vis': vm.is_visible() if vm else None, 'ads_a': round(p.get_editor_property('FurinaVMAds'), 3)}
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            setexp('B_Furina_Experience'); unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview'); S['st'] = 'play'; S['t'] = now + 4; return
        if st == 'play':
            if now >= S['t']: LES().editor_request_begin_play(); S['st'] = 'wait'; S['t'] = now + 90
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None and comp(p, 'FurinaFPVM') is not None: S['st'] = 'settle'; S['t'] = now + 6
            elif now >= S['t']: R['error'] = 'no pawn / no FurinaFPVM'; S['st'] = 'end'
            return
        if p is None: return
        if st == 'settle' and now >= S['t']:
            p.get_editor_property('FurinaFPWanted').set_active(True); S['yaw'] = pc.get_control_rotation().yaw; S['st'] = 'seq'; S['t'] = now + 2.0; return
        if st == 'seq':
            key = KEYS[S['k']]; name, act, wait = STEPS[S['i']]
            if name in PISTOL_ONLY and key not in ('p38', 'p08', 'pp'):
                S['i'] += 1; return
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['yaw']))
            if S['sub'] == 0:
                if now < S['t']: return
                if act == 'key': unreal.get_default_object(unreal.SystemLibrary).call_method('SetStringPropertyByName', (p, 'FurinaPrimaryKey', key))
                elif act == 'fire':
                    a0 = p.get_editor_property('FurinaAmmo'); p.call_method('FurinaRifleShot'); R['events'].append([key, 'fire', a0, p.get_editor_property('FurinaAmmo')])
                    cnt = {}
                    for cp in ('/Game/Furina/FX/BP_HistSmoke.BP_HistSmoke_C', '/Game/Furina/FX/BP_HistFlash.BP_HistFlash_C', '/Game/Furina/M4/BP_M4Flash.BP_M4Flash_C'):
                        try: cnt[cp.rsplit('.', 1)[1]] = len(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, cp)))
                        except Exception as ex: cnt[cp] = str(ex)[:80]
                    try: cnt['vm_on'] = p.get_editor_property('FurinaVMOn')
                    except Exception: pass
                    R['events'].append([key, 'spawned', cnt])
                elif act == 'reload':
                    unreal.get_default_object(unreal.SystemLibrary).call_method('SetIntPropertyByName', (p, 'FurinaAmmo', 0)); p.call_method('FurinaRequestReload'); S['rl0'] = now
                elif act == 'wait_reload':   # 재장전이 끝날 때까지(최대 9초)
                    if p.get_editor_property('FurinaReloading') and now - S['rl0'] < 9.0: return
                    R['events'].append([key, 'reload_done', round(now - S['rl0'], 2), p.get_editor_property('FurinaAmmo')])
                elif act == 'ads_on': p.get_editor_property('FurinaADS').set_active(True)
                elif act == 'aim_off': p.get_editor_property('FurinaADS').set_active(False)
                elif act == 'smoketest':   # 쏜 직후 생긴 연기 액터를 카메라 앞 120cm 로 옮기고 크게·오래
                    p.call_method('FurinaRifleShot')
                    sm = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, '/Game/Furina/FX/BP_HistSmoke.BP_HistSmoke_C'))
                    cam = unreal.GameplayStatics.get_player_camera_manager(w, 0); loc = cam.get_camera_location() + cam.get_actor_forward_vector() * 120.0
                    a_ = sm[-1]; a_.set_actor_location(loc, False, False); a_.set_life_span(30.0); S['test'] = a_
                    m_ = a_.get_component_by_class(unreal.StaticMeshComponent).get_material(0)
                    m_.set_scalar_parameter_value('Density', 1.0); m_.set_scalar_parameter_value('Size', 3.0); m_.set_scalar_parameter_value('Life', 30.0)
                    R['smoketest'] = {'loc': str(loc), 'n': len(sm), 'mat': m_.get_name()}
                elif act == 'smokeinfo':
                    a_ = S.get('test')
                    try:
                        c_ = a_.get_component_by_class(unreal.StaticMeshComponent); m_ = c_.get_material(0)
                        R['smokeinfo'] = {'age': a_.get_editor_property('SmokeAge'), 'mat': m_.get_name(), 'mesh': c_.static_mesh.get_name() if c_.static_mesh else None,
                                          'vis': c_.is_visible(), 'bounds': str(c_.bounds.sphere_radius) if hasattr(c_, 'bounds') else None, 'life': a_.get_life_span(),
                                          'Age_param': m_.get_scalar_parameter_value('Age'), 'Dens': m_.get_scalar_parameter_value('Density'), 'Size': m_.get_scalar_parameter_value('Size')}
                    except Exception as ex: R['smokeinfo'] = str(ex)[:300]
                elif act == 'slomo': unreal.SystemLibrary.execute_console_command(w, 'slomo 0.1')
                elif act == 'slomo1': unreal.SystemLibrary.execute_console_command(w, 'slomo 1')
                elif act == 'sh_on': p.get_editor_property('FurinaShoulder').set_active(True)
                elif act == 'sh_off': p.get_editor_property('FurinaShoulder').set_active(False)
                if name == 'bolt_wait' and key.startswith('kar98k'): wait = BOLT
                S['sub'] = 1; S['t'] = now + wait; return
            if now < S['t']: return
            if S['sub'] == 1:
                if name not in ('rl_wait', 'ads_off', 'bolt_wait', 'sh_off'):
                    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s/fx_%s_%s.png"' % (D, key, name))
                    st_ = status(p)
                    try:
                        sm = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, '/Game/Furina/FX/BP_HistSmoke.BP_HistSmoke_C'))]
                        fl = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, '/Game/Furina/FX/BP_HistFlash.BP_HistFlash_C'))
                        st_['smoke_n'] = len(sm); st_['flash_n'] = len(fl)
                        if sm:
                            a0 = sm[-1]; c0 = a0.get_component_by_class(unreal.StaticMeshComponent); m0 = c0.get_material(0) if c0 else None
                            st_['smoke0'] = {'loc': str(a0.get_actor_location()), 'scale': str(a0.get_actor_scale3d()), 'life': a0.get_life_span(), 'mat': m0.get_name() if m0 else None,
                                             'spawn': m0.get_scalar_parameter_value('Spawn') if isinstance(m0, unreal.MaterialInstanceDynamic) else None,
                                             'dens': m0.get_scalar_parameter_value('Density') if isinstance(m0, unreal.MaterialInstanceDynamic) else None, 'now': unreal.GameplayStatics.get_time_seconds(w)}
                    except Exception as ex: st_['smoke_err'] = str(ex)[:200]
                    try:
                        cam = unreal.GameplayStatics.get_player_camera_manager(w, 0); ct = unreal.Transform(cam.get_camera_location(), cam.get_camera_rotation(), unreal.Vector(1, 1, 1))
                        cs = []
                        for cp in ('/Game/Furina/FX/Pistol/BP_FPVM_9mmCase.BP_FPVM_9mmCase_C', '/Game/Furina/FX/Pistol/BP_FPVM_32Case.BP_FPVM_32Case_C'):
                            for a_ in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, cp)):
                                l_ = unreal.MathLibrary.inverse_transform_location(ct, a_.get_actor_location()); c_ = a_.get_component_by_class(unreal.StaticMeshComponent)
                                v_ = unreal.MathLibrary.inverse_transform_direction(ct, c_.get_physics_linear_velocity()) if c_ else None
                                cs.append([cp.rsplit('.', 1)[1][:-2], [round(l_.x, 1), round(l_.y, 1), round(l_.z, 1)], [round(v_.x), round(v_.y), round(v_.z)] if v_ else None])
                        st_['cases'] = cs
                    except Exception as ex: st_['case_err'] = str(ex)[:200]
                    R['shots'].append([key, name, st_]); save()
                S['sub'] = 2; S['t'] = now + 0.15; return
            S['i'] += 1; S['sub'] = 0; S['t'] = now + 0.05
            if S['i'] >= len(STEPS):
                S['i'] = 0; S['k'] += 1
                if S['k'] >= len(KEYS): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FPVM_CAPTURE_ALL armed')
