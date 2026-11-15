"""PIE: plays the bundle zipline animations (single node) on the player's hidden Manny mesh (CharacterMesh0) one after another and writes key bone positions
(mesh component space, cm) after 12 frames each -> Data/zip_pose_probe.json. The pawn's animation is left in single-node mode - restart PIE afterwards."""
import unreal, json
A = '/Game/3DPlatformerGameBundle/Animations/'
ANIMS = ['One_Handed_Zipline_Anim', 'Two_Handed_Zipline_Anim', 'Zipline_Anim', 'Grab_Pulley_Anim']
BONES = ['pelvis', 'spine_03', 'head', 'upperarm_l', 'lowerarm_l', 'hand_l', 'upperarm_r', 'lowerarm_r', 'hand_r', 'foot_l', 'foot_r']
S = {'n': 0, 'i': 0, 'R': {}}
def comp():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    return [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'CharacterMesh0'][0]
def start(i):
    c = comp(); c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); c.play_animation(unreal.load_asset(A + ANIMS[i]), True)
    c.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES); S['n'] = 0
start(0)
def tick(dt):
    S['n'] += 1
    if S['n'] < 12: return
    c = comp(); T = c.get_world_transform()
    S['R'][ANIMS[S['i']]] = {b: [round(v, 1) for v in unreal.MathLibrary.inverse_transform_location(T, c.get_socket_location(b)).to_tuple()] for b in BONES}
    S['i'] += 1
    if S['i'] >= len(ANIMS):
        unreal.unregister_slate_post_tick_callback(S['h'])
        json.dump(S['R'], open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\zip_pose_probe.json', 'w'), indent=1); print('ZIP_POSE', len(S['R']))
    else: start(S['i'])
S['h'] = unreal.register_slate_post_tick_callback(tick)
