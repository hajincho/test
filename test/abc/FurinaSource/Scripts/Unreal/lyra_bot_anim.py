"""Lyra PIE 중 실행: 봇(마네킹) 폰의 메시/애님 인스턴스/링크된 애님 레이어/속도/현재 몽타주 -> Data/lyra_bot_anim.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_bot_anim.json'
R = {'bots': []}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
        if 'Mannequin' not in p.get_class().get_name(): continue
        m = p.get_editor_property('mesh'); ai = m.get_anim_instance()
        row = {'name': p.get_name(), 'speed': round(p.get_velocity().length()), 'mesh': str(m.get_editor_property('skeletal_mesh_asset').get_name()) if m.get_editor_property('skeletal_mesh_asset') else None,
               'anim_class': ai.get_class().get_name() if ai else None, 'anim_mode': str(m.get_editor_property('animation_mode')),
               'ctrl': p.get_controller().get_class().get_name() if p.get_controller() else None}
        if ai:
            try: row['montage'] = str(ai.get_current_active_montage())
            except Exception as e: row['montage_err'] = str(e)[:60]
            try: row['linked'] = [str(x) for x in m.get_linked_anim_layer_instance_by_class(unreal.AnimInstance)] if False else str(m.get_linked_anim_graph_instances()) if hasattr(m, 'get_linked_anim_graph_instances') else 'n/a'
            except Exception as e: row['linked_err'] = str(e)[:60]
        R['bots'].append(row)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_BOT_ANIM', len(R['bots']), R.get('error', '')[-200:])
