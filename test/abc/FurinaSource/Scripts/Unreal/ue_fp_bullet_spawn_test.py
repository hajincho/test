"""PIE test: spawns BP_FurinaBullet (a) 3 m above the player, flying forward, no instigator; (b) at the player's rifle muzzle with
instigator = player; tracks both for 1 s -> Data/fp_bullet_spawn_test.json (also prints overlapping actors at spawn)."""
import unreal, json, time
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_bullet_spawn_test.json'
S = {'t0': time.time(), 'log': {}}
def main():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    cls = unreal.load_class(None, '/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C')
    fwd = pawn.get_actor_forward_vector(); base = pawn.get_actor_location()
    rifle = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaRifle'][0]
    muz = rifle.get_world_transform().transform_location(unreal.Vector(0, 48.5, 3.1))
    rot = unreal.MathLibrary.make_rot_from_x(fwd)
    a = unreal.EditorLevelLibrary  # unused
    ba = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(w, cls, unreal.Transform(base + unreal.Vector(0, 0, 300), rot, unreal.Vector(1, 1, 1)))
    ba = unreal.GameplayStatics.finish_spawning_actor(ba, unreal.Transform(base + unreal.Vector(0, 0, 300), rot, unreal.Vector(1, 1, 1)))
    bb = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(w, cls, unreal.Transform(muz, rot, unreal.Vector(1, 1, 1)), owner=pawn)
    bb.set_editor_property('instigator', pawn)
    bb = unreal.GameplayStatics.finish_spawning_actor(bb, unreal.Transform(muz, rot, unreal.Vector(1, 1, 1)))
    S['names'] = {'air': ba.get_name(), 'muzzle': bb.get_name()}
    S['muzzle'] = [muz.x, muz.y, muz.z]; S['pawn'] = [base.x, base.y, base.z]
    S['overlap_muzzle'] = [x.get_name() for x in bb.get_overlapping_actors()]
    S['refs'] = (ba, bb)
    del w, pawn, cls, rifle
main(); del main
def tick(dt):
    now = round(time.time() - S['t0'], 3)
    for key, b in zip(('air', 'muzzle'), S['refs']):
        ok = unreal.SystemLibrary.is_valid(b) and not b.is_actor_being_destroyed()
        if ok: p = b.get_actor_location(); S['log'].setdefault(key, []).append([now, round(p.x), round(p.y), round(p.z), round(b.get_velocity().length())])
        else: S['log'].setdefault(key + '_dead', now)
    if now > 1.0:
        unreal.unregister_slate_post_tick_callback(S['h']); S.pop('refs')
        json.dump(S, open(OUT, 'w'), indent=1, default=str); print('SPAWN_TEST done')
S['h'] = unreal.register_slate_post_tick_callback(tick)
