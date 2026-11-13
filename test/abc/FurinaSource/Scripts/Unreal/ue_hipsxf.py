import unreal, json, os, time
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
state = {'t0': time.time(), 'rows': []}
def tick(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
    row = {'t': round(time.time() - state['t0'], 3), 'v': round(pawn.get_velocity().length()), 'idle': round(comp.get_anim_instance().get_curve_value('FurinaIdle'), 3)}
    for b in ('Hips', 'Left-leg', 'Left-knee', 'Left-ankle'):
        x = comp.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
        q = x.rotation; s = x.scale3d; p = x.translation
        row[b] = dict(q=[round(q.x, 3), round(q.y, 3), round(q.z, 3), round(q.w, 3)], s=[round(s.x, 3), round(s.y, 3), round(s.z, 3)], p=[round(p.x, 3), round(p.y, 3), round(p.z, 3)])
    state['rows'].append(row)
    if time.time() - state['t0'] > 5:
        unreal.unregister_slate_post_tick_callback(state['h'])
        json.dump(state['rows'], open(os.path.join(S, 'ue_hipsxf.json'), 'w'), indent=0)
state['h'] = unreal.register_slate_post_tick_callback(tick)
