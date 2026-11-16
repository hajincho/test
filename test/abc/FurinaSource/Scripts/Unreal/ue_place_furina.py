"""Editor (current level open): puts the existing player character /Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP (Furina, rifle, HUD, ...) on the walkable floor of the
current level and sets Auto Possess Player 0 (the same way the old ExampleLevel has it). The spot is searched with vertical line traces around the centre of the level's post process volume / fog (else the origin):
floor normal up (>0.9), at least 230 cm of free height above it, and a flat 300 cm neighbourhood. Existing pawns of that class in the level are left alone unless argv[1] == 'replace'.
usage: py ue_place_furina.py [replace] [x y]  (x y: force the XY of the search centre)   -> Data/place_furina.json ; the level is saved"""
import unreal, json, sys, math, traceback
R = {}
CLS_PATH = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
try:
    args = sys.argv[1:]; replace = 'replace' in args; nums = [float(a) for a in args if a != 'replace']
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); R['world'] = w.get_path_name()
    acts = eas.get_all_level_actors(); cls = unreal.load_class(None, CLS_PATH + '.ThirdPersonCharacter_BP_C'); assert cls, 'class'
    old = [a for a in acts if a.get_class() == cls]; R['existing'] = [a.get_actor_label() for a in old]
    if old and replace:
        for a in old: eas.destroy_actor(a)
        old = []
    if old: R['note'] = 'character already in the level, nothing placed'
    else:
        direct = len(nums) >= 3
        if len(nums) >= 2: cx, cy, cz = nums[0], nums[1], 0.0
        else:
            c = [a.get_actor_location() for a in acts if a.get_class().get_name() in ('PostProcessVolume', 'ExponentialHeightFog')]
            cx = sum(p.x for p in c) / len(c) if c else 0.0; cy = sum(p.y for p in c) / len(c) if c else 0.0; cz = sum(p.z for p in c) / len(c) if c else 0.0
        R['center'] = [cx, cy, cz]
        def trace(a, b):
            r = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            return (r[1] if isinstance(r, tuple) else None) if (r[0] if isinstance(r, tuple) else r) else None
        def floor_at(x, y, z0):
            h = trace(unreal.Vector(x, y, z0), unreal.Vector(x, y, z0 - 800))
            if h is None: return None
            n = h.impact_normal; p = h.impact_point
            if n.z < 0.9: return None
            up = trace(unreal.Vector(p.x, p.y, p.z + 5), unreal.Vector(p.x, p.y, p.z + 400))
            if up is not None and up.impact_point.z - p.z < 230: return None
            return p.z
        if direct:      # line traces return nothing in the editor world of this level, so an explicit spawn point (x y z = capsule centre height) can be given: the pawn falls to the floor in PIE
            x, y, z = nums[0], nums[1], nums[2] - 100.0; best_yaw = float(nums[3]) if len(nums) > 3 else 0.0; best_len = None; R['direct'] = True
        else:
            best = None; cand = []
            for z0 in (cz + 200, cz + 600, cz + 1200):
                for dx in range(-3000, 3001, 250):
                    for dy in range(-3000, 3001, 250):
                        z = floor_at(cx + dx, cy + dy, z0)
                        if z is None: continue
                        ok = True
                        for ex, ey in ((150, 0), (-150, 0), (0, 150), (0, -150)):
                            z2 = floor_at(cx + dx + ex, cy + dy + ey, z + 120)
                            if z2 is None or abs(z2 - z) > 12: ok = False; break
                        if ok: cand.append((math.hypot(dx, dy), cx + dx, cy + dy, z))
                if cand: break
            cand.sort(); R['candidates'] = len(cand)
            assert cand, 'no flat floor found'
            _, x, y, z = cand[0]; R['floor'] = [x, y, z]
            # face along the direction with the longest free run (the tunnel axis)
            best_yaw, best_len = 0.0, -1.0
            for yaw in range(0, 360, 30):
                d = unreal.Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)
                h = trace(unreal.Vector(x, y, z + 120), unreal.Vector(x + d.x * 6000, y + d.y * 6000, z + 120)); length = 6000 if h is None else (h.impact_point - unreal.Vector(x, y, z + 120)).length()
                if length > best_len: best_len, best_yaw = length, float(yaw)
            R['yaw'] = best_yaw; R['free_run_cm'] = best_len
        pawn = eas.spawn_actor_from_class(cls, unreal.Vector(x, y, z + 100), unreal.Rotator(roll=0, pitch=0, yaw=best_yaw)); assert pawn, 'spawn'
        pawn.set_actor_label('Furina_Player'); pawn.set_editor_property('auto_possess_player', unreal.AutoReceiveInput.PLAYER0); R['placed'] = pawn.get_actor_label()
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); R['saved'] = les.save_current_level()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\place_furina.json', 'w'), indent=1); print('PLACE_FURINA', R.get('placed', R.get('note')), R.get('error', '')[-300:])
