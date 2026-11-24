"""PIE 확인(2026-11-23): 시작 외형 = Sparxie, 3인칭 앞·옆 캡처, 1인칭 캡처, 발 높이 -> Data/robin_pie.json, Data/sparxie_<단계>.png
 에디터 창이 뒤에 있으면 PIE 가 초당 3프레임으로 느려지므로 실행 전에 에디터 창을 앞으로."""
import unreal, json, os, sys, time, traceback
D = (unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + 'FurinaSource/Data').replace(chr(92), '/')
D = next((arg.split('=', 1)[1] for arg in sys.argv[1:] if arg.startswith('out=')), D)
os.makedirs(D, exist_ok=True)
OUT = D + '/robin_pie.json'
R = {'shots': []}; S = {'st': 'open', 't': 0, 'i': 0}
LES = lambda: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
STEPS = [('tp_front', 180.0, False, 1.5), ('tp_side', 90.0, False, 1.2), ('tp_back', 0.0, False, 1.2), ('fp', 0.0, True, 2.0)]
SKIN_COMPARE = 'skin_compare' in sys.argv[1:]
SKIN_VERIFY = 'skin_verify' in sys.argv[1:]
if SKIN_COMPARE:
    STEPS = [('tp_reference', 90.0, False, 2.0), ('fp_before', 0.0, True, 2.0), ('fp_after', 0.0, True, 2.0)]
    CANDIDATE = unreal.load_asset('/Game/Furina/Classes/Robin/Materials/MI_Robin_FP_Mat18')
    assert CANDIDATE, 'Robin 1인칭 피부 보정 재질을 먼저 준비해야 합니다.'
elif SKIN_VERIFY:
    STEPS = [('fp_applied', 0.0, True, 2.0)]
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def comp(p, name, cls=unreal.ActorComponent):
    for c in p.get_components_by_class(cls):
        if c.get_name() == name: return c
def tick(dt):
    try:
        now = time.time(); st = S['st']
        if st == 'done': return
        if st == 'open':
            S['st'] = 'loading'
            unreal.get_default_object(unreal.LyraDeveloperSettings).set_editor_property('experience_override', unreal.PrimaryAssetId(unreal.PrimaryAssetType('LyraExperienceDefinition'), 'B_Furina_Experience'))
            editor_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            if editor_world.get_name() != 'L_DefaultEditorOverview':
                unreal.EditorLoadingAndSavingUtils.load_map('/Game/System/DefaultEditorMap/L_DefaultEditorOverview')
            S['st'] = 'play'; S['t'] = time.time() + 4; return
        if st == 'loading': return
        if st == 'play':
            if now >= S['t']: S['st'] = 'wait'; S['t'] = now + 150; LES().editor_request_begin_play()
            return
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); p = unreal.GameplayStatics.get_player_pawn(w, 0) if w else None
        pc = unreal.GameplayStatics.get_player_controller(w, 0) if w else None
        if st == 'wait':
            if p is not None and comp(p, 'FurinaMesh') is not None: S['st'] = 'settle'; S['t'] = now + 6
            elif now >= S['t']: R['error'] = 'no pawn'; S['st'] = 'end'
            return
        if p is None: return
        if st == 'settle' and now >= S['t']:
            m = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent)
            if SKIN_COMPARE or SKIN_VERIFY:
                unreal.get_default_object(unreal.SystemLibrary).call_method('SetStringPropertyByName', (p, 'FurinaPrimaryKey', 'mp40'))
            R['look'] = str(p.get_editor_property('FurinaLook')); R['mesh'] = m.get_skeletal_mesh_asset().get_name() if m.get_skeletal_mesh_asset() else None
            R['n_mats'] = m.get_num_materials(); R['mats'] = [m.get_material(i).get_name() if m.get_material(i) else None for i in range(m.get_num_materials())][:40]
            S['yaw0'] = p.get_actor_rotation().yaw; S['st'] = 'seq'; S['sub'] = 0; S['t'] = now; return
        if st == 'seq':
            name, dyaw, fp, wait = STEPS[S['i']]
            if S['sub'] == 0:
                p.get_editor_property('FurinaFPWanted').set_active(fp)
                if name == 'fp_after':
                    vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent)
                    slot = vm.get_material_index('CARobin_Mat18')
                    assert slot >= 0, 'Robin 1인칭 피부 슬롯을 찾지 못했습니다.'
                    vm.set_material(slot, CANDIDATE)
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8.0 if not fp else 0.0, yaw=S['yaw0'] + dyaw)); S['sub'] = 1; S['t'] = now + wait; return
            if now < S['t']: return
            if S['sub'] == 1:
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-8.0 if not fp else 0.0, yaw=S['yaw0'] + dyaw))
                unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s/robin_%s.png"' % (D, name))
                m = comp(p, 'FurinaMesh', unreal.SkeletalMeshComponent); info = {'name': name}
                try:
                    floor = p.get_actor_location().z - p.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
                    info['toe_above_floor'] = [round(m.get_socket_location(b).z - floor, 1) for b in ('Left-toe', 'Right-toe')]
                    info['head_above_floor'] = round(m.get_socket_location('Head').z - floor, 1)
                except Exception as ex: info['err'] = str(ex)[:200]
                vm = comp(p, 'FurinaFPVM', unreal.SkeletalMeshComponent)
                if vm and vm.get_skeletal_mesh_asset():
                    info['vm'] = vm.get_skeletal_mesh_asset().get_name(); info['vm_vis'] = vm.is_visible()
                    info['vm_mats'] = {i: (vm.get_material(i).get_name() if vm.get_material(i) else None) for i in range(vm.get_num_materials())}
                R['shots'].append(info); save(); S['sub'] = 2; S['t'] = now + 0.4; return
            S['i'] += 1; S['sub'] = 0
            if S['i'] >= len(STEPS): S['st'] = 'end'; S['t'] = now + 0.5
            return
        if st == 'end' and now >= S['t']:
            R['done'] = True; save(); S['st'] = 'ending'; S['t'] = now + 5; LES().editor_request_end_play(); return
        if st == 'ending' and now >= S['t']:
            S['st'] = 'done'; unreal.unregister_slate_post_tick_callback(S['h'])
    except Exception:
        R['error'] = traceback.format_exc(); R['done'] = True; save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); save(); print('SPARXIE_PIE armed')
