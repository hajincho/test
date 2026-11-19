"""Lyra 에디터(`py <파일>`): 권총 재장전/발사 몽타주의 세그먼트(참조 시퀀스/구간/속도)와 곡선, 그리고 BP 의 P2_PlaySlot 노드가 쓰는 몽타주를 조사.  -> Data/lyra_pistol_montage_probe.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_pistol_montage_probe.json'
R = {}
def run():
    AL = unreal.AnimationLibrary; F = unreal.RawCurveTrackTypes.RCT_FLOAT
    for nm in ('AM_Furina_Pistol_Reload', 'AM_Furina_Pistol_Reload1', 'AM_Furina_Pistol_Fire', 'AM_Furina_Pistol_Fire1', 'AM_Furina_Pistol_Equip'):
        a = unreal.load_asset('/Game/Furina/P220/Anim/' + nm); row = {'len': a.get_play_length(), 'segs': [], 'curves': [str(x) for x in AL.get_animation_curve_names(a, F)]}
        for tr in a.get_editor_property('slot_anim_tracks'):
            for s in tr.get_editor_property('anim_track').get_editor_property('anim_segments'):
                ref = s.get_editor_property('anim_reference'); row['segs'].append({'ref': ref.get_path_name() if ref else None, 'start': s.get_editor_property('anim_start_time'), 'end': s.get_editor_property('anim_end_time'), 'rate': s.get_editor_property('anim_play_rate'), 'slot': str(tr.get_editor_property('slot_name'))})
        try: row['blend_in'] = str(a.get_editor_property('blend_in')); row['blend_out'] = str(a.get_editor_property('blend_out'))
        except Exception: pass
        R[nm] = row
    for nm in ('Furina_Pistol_Reload', 'Furina_Pistol_Reload1', 'Furina_Pistol_Reload_Additive'):
        a = unreal.load_asset('/Game/Furina/P220/Anim/' + nm); R[nm] = {'len': a.get_play_length(), 'curves': [str(x) for x in AL.get_animation_curve_names(a, F)][:12], 'rate_scale': a.get_editor_property('rate_scale')}
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    for n in ed.list_all_nodes():
        nm = n.get_name()
        if nm.startswith('P2_PlaySlot'):
            R['node_' + nm] = [[str(p.get_pin_name()), str(p.get_pin_value())[:150], [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()][:3]] for p in n.list_all_pins()]
    del ed, bp
try: run()
except Exception: R['error'] = traceback.format_exc()[-800:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_PISTOL_MONTAGE_PROBE', R.get('error', 'ok'))
import gc; gc.collect()
