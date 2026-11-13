import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    res['world'] = str(w)
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    res['pawn'] = pawn.get_name(); res['pawn_loc'] = str(pawn.get_actor_location())
    for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):
        d = dict(visible=c.is_visible(), loc=str(c.get_world_location()), bounds=str(c.bounds) if hasattr(c, 'bounds') else None)
        names = ['Hips', 'Head', 'Left-ankle', 'HB1_7_2', 'HB2_18_1'] if c.get_name() == 'FurinaMesh' else ['pelvis', 'head', 'foot_l']
        for n in names:
            d[n] = str(c.get_socket_location(n))
        try: d['anim'] = str(c.get_anim_instance())
        except Exception as e: d['anim'] = repr(e)
        res[c.get_name()] = d
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(S, 'ue_pie.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('PIE_DONE')
