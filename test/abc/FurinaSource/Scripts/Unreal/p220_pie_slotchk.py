"""PIE: DefaultSlot 몽타주가 실제로 평가되는지(슬롯 활성/가중치) 확인."""
import unreal, json, time, traceback
OUT = r'L:\Saved\Scratch\p220_slotchk.json'
R = {'rows': []}; S = {'stage': 0, 't0': 0.0}
def save(): json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
def tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None: return
        now = time.time(); p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if S['stage'] == 0:
            if p is None or p.get_class().get_name() != 'ThirdPersonCharacter_BP_C': return
            S['p'] = p; S['t0'] = now; S['stage'] = 1; return
        p = S['p']; inst = p.get_editor_property('FurinaMesh').get_anim_instance(); el = now - S['t0']
        if S['stage'] == 1 and el > 2.0:
            R['slot_active_before'] = inst.is_slot_active('DefaultSlot'); R['slots_curr_montage_before'] = str(inst.get_current_active_montage())
            R['fp_idle_ok'] = True
            for nm in ('AM_Furina_FP_Fire',):
                m = unreal.load_asset('/Game/Furina/FP/Anim/' + nm); inst.montage_play(m, 1.0); R['fp_montage_played'] = nm
            S['t0'] = now; S['stage'] = 2
        elif S['stage'] == 2 and el > 0.25:
            R['rows'].append(['rifle FP_Fire montage', inst.is_slot_active('DefaultSlot'), round(float(inst.blueprint_get_slot_montage_local_weight('DefaultSlot')), 3), str(inst.get_current_active_montage())[:60]]); S['t0'] = now; S['stage'] = 3
        elif S['stage'] == 3 and el > 1.5:
            m = inst.play_slot_animation_as_dynamic_montage(unreal.load_asset('/Game/Furina/P220/Anim/Furina_Pistol_Idle_Hipfire'), 'DefaultSlot', 0.2, 0.2, 1.0, 9999, -1.0, 0.0); S['t0'] = now; S['stage'] = 4
        elif S['stage'] == 4 and el > 0.6:
            R['rows'].append(['pistol idle dyn montage', inst.is_slot_active('DefaultSlot'), round(float(inst.blueprint_get_slot_montage_local_weight('DefaultSlot')), 3), str(inst.get_current_active_montage())[:60]])
            S['stage'] = 9; save(); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); unreal.unregister_slate_post_tick_callback(S['h'])
        save()
    except Exception:
        R['error'] = traceback.format_exc(); save()
        try: unreal.unregister_slate_post_tick_callback(S['h'])
        except Exception: pass
S['h'] = unreal.register_slate_post_tick_callback(tick); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); save(); print('P220_SLOTCHK armed')
