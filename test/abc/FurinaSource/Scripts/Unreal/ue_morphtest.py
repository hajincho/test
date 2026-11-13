"""Temporary face check: spawns SK_Furina high above the level, sets one morph, points the editor camera at the face.
usage (console): py ue_morphtest.py <morph name or 'none' or 'cleanup'>"""
import unreal, sys
arg = sys.argv[1] if len(sys.argv) > 1 else 'IdleBlink'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LABEL = 'FurinaMorphTest_TEMP'
actors = [a for a in eas.get_all_level_actors() if a.get_actor_label() == LABEL]
if arg == 'cleanup':
    for a in actors: eas.destroy_actor(a)
    print('MORPHTEST cleaned', len(actors))
else:
    if actors: actor = actors[0]
    else:
        actor = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 20000), unreal.Rotator(0, 0, 0))
        actor.set_actor_label(LABEL)
        comp = actor.skeletal_mesh_component
        comp.set_skinned_asset_and_update(unreal.load_asset('/Game/Furina/SK_Furina'))
        comp.set_editor_property('update_animation_in_editor', True)
    comp = actor.skeletal_mesh_component
    comp.clear_morph_targets()
    if arg != 'none': comp.set_morph_target(arg, 1.0)
    # face at ~ (0, 1, 20135); mesh faces +Y in component space
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(0, 38, 20136), unreal.Rotator(pitch=0, yaw=-90, roll=0))
    print('MORPHTEST', arg)
