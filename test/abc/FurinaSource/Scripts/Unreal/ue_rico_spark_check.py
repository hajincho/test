import unreal, json
c = unreal.load_class(None, '/Game/Furina/M4/BP_RicoSpark.BP_RicoSpark_C'); d = unreal.get_default_object(c)
R = {'cdo_life': d.get_editor_property('initial_life_span'), 'class': str(c)}
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if w is not None:
    R['instances'] = [[a.get_name(), a.get_life_span(), a.get_editor_property('initial_life_span')] for a in unreal.GameplayStatics.get_all_actors_of_class(w, c)]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\rico_spark_check.json', 'w'), indent=1); print('CHECK', R)
