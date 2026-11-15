"""Saves every dirty content package (not maps) and lists what was dirty -> Data/save_all.json"""
import unreal, json
dirty = [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
json.dump(dict(dirty=dirty, saved=ok), open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\save_all.json', 'w'), indent=1); print('SAVE_ALL', dirty, ok)
