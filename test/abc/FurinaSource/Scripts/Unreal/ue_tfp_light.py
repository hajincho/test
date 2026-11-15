import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.SceneCapture2D):
 c=a.get_component_by_class(unreal.SceneCaptureComponent2D);c.set_editor_property('capture_every_frame',False);c.set_editor_property('capture_on_movement',False)
for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.PointLight):
 c=a.get_component_by_class(unreal.PointLightComponent);c.set_intensity(10000);c.set_editor_property('attenuation_radius',2000.)
