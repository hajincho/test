"""Temporary side-by-side face check (left: no morph, right: IdleBlink=1). 'cleanup' removes them."""
import unreal, sys
arg = sys.argv[1] if len(sys.argv) > 1 else 'IdleBlink'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('FurinaMorph'): eas.destroy_actor(a)
if arg != 'cleanup':
    for i, (x, morph) in enumerate(((-20, None), (20, arg))):
        a = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(x, 0, 20000), unreal.Rotator(0, 0, 0))
        a.set_actor_label('FurinaMorphPair_%d' % i)
        c = a.skeletal_mesh_component
        c.set_skinned_asset_and_update(unreal.load_asset('/Game/Furina/SK_Furina'))
        c.set_editor_property('update_animation_in_editor', True)
        if morph:
            for m in morph.split(','): c.set_morph_target(m, 1.0)
    # light from the camera side so the faces are readable
    l = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(0, 80, 20140), unreal.Rotator(0, 0, 0))
    l.set_actor_label('FurinaMorphLight')
    l.point_light_component.set_intensity(40)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(0, 75, 20134), unreal.Rotator(pitch=0, yaw=-90, roll=0))
print('MORPHPAIR', arg)
