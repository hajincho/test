"""Editor: removes the level's background music: every AmbientSound actor of the open level is listed (label, sound asset) and destroyed, then the level is saved.
usage: py ue_remove_bgm.py [list]   ('list' only reports)  -> Data/remove_bgm.json"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    R = {'removed': [], 'kept': []}
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.AmbientSound):
            comp = a.get_component_by_class(unreal.AudioComponent); snd = comp.get_editor_property('sound') if comp else None
            info = dict(actor=a.get_name(), label=a.get_actor_label(), sound=snd.get_path_name() if snd else None, auto_activate=bool(comp.get_editor_property('auto_activate')) if comp else None)
            if len(sys.argv) > 1 and sys.argv[1] == 'list': R['kept'].append(info); continue
            R['removed'].append(info); eas.destroy_actor(a)
    if R['removed']: R['level_saved'] = unreal.EditorLevelLibrary.save_current_level()
    json.dump(R, open(D + r'\remove_bgm.json', 'w'), indent=1, ensure_ascii=False); print('REMOVE_BGM', R)
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\remove_bgm.json', 'w'))
