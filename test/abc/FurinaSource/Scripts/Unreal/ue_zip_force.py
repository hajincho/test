"""PIE preview of the rappel pose without riding a zipline: plays the bundle's One_Handed_Zipline_Anim (single node) on the hidden Manny mesh and keeps the
FurinaZip / FurinaSpecial flag components active every frame for <seconds>, then releases them (and restores the Manny animation blueprint). usage: py ue_zip_force.py [seconds] [anim]"""
import unreal, sys, time
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
ANIM = sys.argv[2] if len(sys.argv) > 2 else 'One_Handed_Zipline_Anim'
S = {'t0': time.time()}
def parts():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    return pawn, [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'CharacterMesh0'][0]
pawn, m = parts()
S['cls'] = m.get_editor_property('anim_class'); m.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
m.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); m.play_animation(unreal.load_asset('/Game/3DPlatformerGameBundle/Animations/' + ANIM), True)
del pawn, m
def tick(dt):
    pawn, m = parts()
    for tag in ('FurinaZip', 'FurinaSpecial'):
        for c in pawn.get_components_by_tag(unreal.ActorComponent, tag): c.set_active(True, False)
    if time.time() - S['t0'] > DUR:
        unreal.unregister_slate_post_tick_callback(S['h'])
        for tag in ('FurinaZip', 'FurinaSpecial'):
            for c in pawn.get_components_by_tag(unreal.ActorComponent, tag): c.set_active(False, False)
        m.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT); m.set_editor_property('anim_class', S['cls']); print('ZIP_FORCE done')
    del pawn, m
S['h'] = unreal.register_slate_post_tick_callback(tick)
