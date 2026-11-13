import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    comp = [c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]
    ref = comp.get_skinned_asset().get_editor_property('skeleton').get_reference_pose()
    names = [str(n) for n in unreal.AnimPoseExtensions.get_bone_names(ref)]
    worst = []
    for n in names:
        p = str(comp.get_parent_bone(n))
        if p in ('None', '') : continue
        live = (comp.get_socket_location(n) - comp.get_socket_location(p)).length()
        rest = unreal.AnimPoseExtensions.get_bone_pose(ref, n, unreal.AnimPoseSpaces.LOCAL).translation.length()
        worst.append((round(live - rest * 100, 2), n, round(rest * 100, 2)))
    worst.sort(key=lambda t: -abs(t[0]))
    res['worst_stretch'] = worst[:8]
    # cloth vs legs: closest HB joint to each thigh/shin segment
    def seg_dist(p, a, b):
        ab = b - a; t = max(0, min(1, (p - a).dot(ab) / max(ab.dot(ab), 1e-6)))
        return (p - (a + ab * t)).length()
    legs = []
    for s in ('Left', 'Right'):
        L = [comp.get_socket_location(s + x) for x in ('-leg', '-knee', '-ankle')]
        legs += [(L[0], L[1], 8.2), (L[1], L[2], 5.5)]
    pen = []
    for n in names:
        if not n.startswith('HB'): continue
        p = comp.get_socket_location(n)
        d = min(seg_dist(p, a, b) - r for a, b, r in legs)
        pen.append((round(d, 2), n))
    pen.sort()
    res['closest_to_legs'] = pen[:8]
    res['pawn'] = str(pawn.get_actor_location())
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_cloth_check.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('CLOTH_CHECK_DONE')
