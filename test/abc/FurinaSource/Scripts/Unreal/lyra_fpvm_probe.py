"""Lyra 에디터(`py <파일> [태그]`, run_ue_probe.ps1 백그라운드): Kar98k 1인칭 뷰모델 확인.
 무기 키 kar98k(무기창이 넣는 FurinaPrimaryKey 를 직접 설정) -> 1인칭 -> 대기 캡처 -> 사격(볼트 조작 중 캡처, 0.3초 뒤 다시 쏴도 막히는지, 1.3초 뒤 다시 쏘기)
 -> 재장전(클립) 단계 캡처 -> 정조준 캡처 -> 3인칭 복귀(뷰모델 꺼짐, 소총 다시 보임)
 캡처: Data/fpvm_<태그>_<단계>.png   기록: Data/lyra_fpvm_probe_<태그>.json"""
import unreal, json, sys, time, traceback, math
TAG = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith('.py') else 'now'
D = 'C:/Users/fromj/Downloads/test/test/abc/FurinaSource/Data'; OUT = D + '/lyra_fpvm_probe_%s.json' % TAG
R = {'tag': TAG, 'shots': [], 'events': []}; S = {'st': 'open', 't': 0, 'i': 0, 'sub': 0, 't0': None}
# (이름, 동작, 대기초)
STEPS = [('hip', 'key', 2.0), ('hip2', None, 1.0), ('fire_kick', 'fire', 0.05), ('fire_block', 'fire', 0.05), ('fire_lift', None, 0.15), ('fire_back', None, 0.1), ('fire_push', None, 0.1),
         ('fire_end', None, 0.7), ('fire2', 'fire', 0.08), ('fire2_end', None, 1.4),
         ('rl_open', 'reload', 0.4), ('rl_pouch', None, 0.45), ('rl_guide', None, 0.3), ('rl_push', None, 0.3), ('rl_close', None, 0.35), ('rl_end', None, 1.2),
         ('ads', 'ads_on', 1.2), ('ads_fire', 'fire', 0.08), ('ads_bolt', None, 0.3), ('ads_end', None, 1.2), ('hip3', 'aim_off', 1.2), ('tp', 'tp', 2.0)]
WKEY = TAG.split('_')[1] if TAG.startswith('k_') else ('g43' if TAG.startswith('g') else 'kar98k')
if TAG.startswith('k_'):   # 무기 키 일반 점검(2026-11-21): 대기 -> 사격 -> 재장전 단계 -> 정조준. kar98k/g43 은 2발 쏜 뒤 재장전(낱발 탄 방향 확인)
    LOOSE = WKEY in ('kar98k', 'g43')
    STEPS = [('hip', 'key', 2.5), ('fire1', 'fire', 0.06), ('fire2', 'fire', 0.12 if not LOOSE else 1.4), ('fire3', 'fire', 0.12 if not LOOSE else 1.5)]
    if LOOSE:   # 낱발: 한 발 주기 0.63초(1.04초부터), 탄이 홈에 닿는 때(주기 0.26~0.38)에 맞춤. 캡처 한 번에 약 0.37초가 더 걸림
        STEPS += [('rl_a', 'reload_keep', 0.52), ('rl_b', None, 0.0), ('rl_c', None, 0.0), ('rl_d', None, 0.0), ('rl_e', None, 0.45), ('rl_f', None, 0.6), ('rl_end', None, 1.5),
                  ('ads', 'ads_on', 1.2), ('ads_fire', 'fire', 0.06), ('hip3', 'aim_off', 1.0)]
    else: STEPS += [('rl_a', 'reload', 0.35), ('rl_b', None, 0.35), ('rl_c', None, 0.35), ('rl_d', None, 0.35), ('rl_e', None, 0.45), ('rl_f', None, 0.6), ('rl_end', None, 1.5),
              ('ads', 'ads_on', 1.2), ('ads_fire', 'fire', 0.06), ('hip3', 'aim_off', 1.0)]
if TAG.startswith('gm'):   # 재질 덮어쓰기 확인
    STEPS = [('hip', 'key', 2.5), ('hip_clear', 'clearov', 1.0)]
elif TAG.startswith('gn'):   # 노멀맵 시험: 원래 / 평평한 노멀 / 위에서 내려다본 각도
    STEPS = [('hip', 'key', 2.5), ('hip_flat', 'flatnorm', 1.0), ('hip_orig', 'orignorm', 1.0)]
elif WKEY == 'g43' and not TAG.startswith('k_'):
    STEPS = [('hip', 'key', 2.0), ('fire_kick', 'fire', 0.03), ('fire_semi2', 'fire', 0.35), ('fire_end', None, 0.6),
             ('rl_open', 'reload', 0.35), ('rl_pouch', None, 0.2), ('rl_guide1', None, 0.35), ('rl_push1', None, 0.3), ('rl_toss1', None, 0.3), ('rl_guide2', None, 0.5),
             ('rl_push2', None, 0.4), ('rl_close', None, 0.6), ('rl_end', None, 1.0), ('ads', 'ads_on', 1.2), ('ads_fire', 'fire', 0.05), ('hip3', 'aim_off', 1.0),
             ('swap_k98', 'key2', 1.5), ('tp', 'tp', 2.0)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def setexp(n): unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), n))
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def comp(p, name, cls=unreal.SceneComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def status(p, w):
    vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent); rf = comp(p, 'FurinaRifle'); cam = comp(p, 'FPCamera')
    e = {'vm_vis': vm.is_visible() if vm else None, 'rifle_vis': rf.is_visible() if rf else None, 'on': p.get_editor_property('FurinaVMOn'), 'idle': p.get_editor_property('FurinaVMIdle'),
         'busy_left': round(p.get_editor_property('FurinaVMBusy') - unreal.GameplayStatics.get_time_seconds(w), 3), 'ads_a': round(p.get_editor_property('FurinaVMAds'), 3),
         'ammo': p.get_editor_property('FurinaAmmo'), 'wid': str(p.get_editor_property('FurinaGameWeaponId')), 'loose': p.get_editor_property('FurinaLooseReload'), 'anim_rl': (p.get_editor_property('FurinaVMAnimReload').get_name() if p.get_editor_property('FurinaVMAnimReload') else None), 'valid': p.get_editor_property('FurinaVMValid'), 'mesh': (vm.get_skeletal_mesh_asset().get_name() if vm and vm.get_skeletal_mesh_asset() else None), 'rl': bool(p.get_editor_property('FurinaReloading')), 'fp': cam.is_active() if cam else None}
    if vm and cam:
        ct = cam.get_world_transform();
        for b in ('VM_Gun', 'VM_Bolt', 'VM_Clip', 'Right wrist', 'Left wrist'):
            try:
                l = unreal.MathLibrary.inverse_transform_location(ct, vm.get_socket_location(b)); e[b] = [round(l.x, 2), round(l.y, 2), round(l.z, 2)]
            except Exception as ex: e[b] = str(ex)[:60]
        rel = vm.get_relative_transform(); e['rel_loc'] = [round(rel.translation.x, 2), round(rel.translation.y, 2), round(rel.translation.z, 2)]
    return e
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
        gt = unreal.GameplayStatics.get_time_seconds(w)
        if st == 'settle' and now >= S['t']:
            R['before'] = status(p, w); p.get_editor_property('FurinaFPWanted').set_active(True); S['yaw'] = pc.get_control_rotation().yaw; S['st'] = 'seq'; S['t'] = now + 2.0; S['t0'] = gt; return
        if st == 'seq':
            name, act, wait = STEPS[S['i']]
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=S['yaw']))
            if S['sub'] == 0:
                if now < S['t']: return
                if act in ('key', 'key2'): unreal.get_default_object(unreal.SystemLibrary).call_method('SetStringPropertyByName', (p, 'FurinaPrimaryKey', WKEY if act == 'key' else 'kar98k'))
                elif act == 'fire':
                    a0 = p.get_editor_property('FurinaAmmo'); p.call_method('FurinaRifleShot'); R['events'].append([name, round(gt - S['t0'], 3), 'ammo', a0, p.get_editor_property('FurinaAmmo')])
                elif act == 'reload_keep': unreal.get_default_object(unreal.SystemLibrary).call_method('SetIntPropertyByName', (p, 'FurinaAmmo', 3)); p.call_method('FurinaRequestReload'); R['events'].append(['reload_keep', round(gt - S['t0'], 3)])
                elif act == 'reload': unreal.get_default_object(unreal.SystemLibrary).call_method('SetIntPropertyByName', (p, 'FurinaAmmo', 0)); p.call_method('FurinaRequestReload'); R['events'].append(['reload', round(gt - S['t0'], 3)])
                elif act == 'ads_on': p.get_editor_property('FurinaADS').set_active(True)
                elif act == 'aim_off': p.get_editor_property('FurinaADS').set_active(False)
                elif act == 'clearov':
                    vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent)
                    R['ov_before'] = [m.get_name() if m else None for m in vm.get_editor_property('override_materials')]; R['mats_before'] = [m.get_name() if m else None for m in vm.get_materials()]
                    vm.set_editor_property('override_materials', []); vm.set_skinned_asset_and_update(vm.get_skinned_asset(), True)
                    R['ov_after'] = [m.get_name() if m else None for m in vm.get_editor_property('override_materials')]; R['mats_after'] = [m.get_name() if m else None for m in vm.get_materials()]
                elif act in ('flatnorm', 'orignorm'):
                    vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent)
                    if act == 'flatnorm':
                        S['orig'] = vm.get_material(2); mid = vm.create_dynamic_material_instance(2, S['orig'])
                        mid.set_texture_parameter_value('NormalTex', unreal.load_asset('/Game/Furina/Weapons/Materials/T_FW_FlatNormal')); R['mat2'] = S['orig'].get_name()
                    else: vm.set_material(2, S['orig'])
                elif act == 'tp': p.get_editor_property('FurinaFPWanted').set_active(False)
                S['sub'] = 1; S['t'] = now + wait; return
            if now < S['t']: return
            if S['sub'] == 1:
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s/fpvm_%s_%s.png"' % (D, TAG, name))
                R['shots'].append([name, round(gt - S['t0'], 3), status(p, w)]); S['sub'] = 2; S['t'] = now + 0.15; save(); return
            S['i'] += 1; S['sub'] = 0; S['t'] = now + 0.05
            if S['i'] >= len(STEPS): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); LES().editor_request_end_play(); S['st'] = 'ending'; S['t'] = now + 6; return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('LYRA_FPVM_PROBE armed', TAG)
