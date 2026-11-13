import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    res['vel'] = pawn.get_velocity().length()
    for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):
        ai = c.get_anim_instance()
        d = {}
        for cv in ('FurinaIdle', 'IdleBlink'):
            try: d[cv] = ai.get_curve_value(cv)
            except Exception as e: d[cv] = repr(e)
        z0 = c.get_world_location().z
        if c.get_name() == 'FurinaMesh':
            for b in ('Hips', 'Head', 'Left-ankle', 'Right-ankle', 'Left-toe', 'Right-toe', 'HB2_18_1', 'F_17_1_L', 'HB1_7_4'):
                p = c.get_socket_location(b); d[b] = [round(p.x, 1), round(p.y, 1), round(p.z - z0, 1)]
        res[c.get_name()] = d
except Exception:
    res['error'] = traceback.format_exc()
out = os.path.join(S, 'ue_pie2.json')
hist = json.load(open(out)) if os.path.exists(out) else []
hist.append(res)
json.dump(hist, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('PIE2_DONE')
