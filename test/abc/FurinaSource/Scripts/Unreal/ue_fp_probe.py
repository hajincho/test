"""PIE probe for the rifle setup: attachment, HUD class, active cameras, hand-to-rifle distances."""
import unreal, json, os, traceback
def main():
    R = {}
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        pc = unreal.GameplayStatics.get_player_controller(w, 0)
        R['hud'] = str(pc.get_hud()) if hasattr(pc, 'get_hud') else 'n/a'
        try:
            hud = pc.get_hud(); R['hud_props'] = {k: str(hud.get_editor_property(k)) for k in ('show_hud', 'show_overlays', 'show_debug_info')}
        except Exception as e: R['hud_props'] = repr(e)[:200]
        comps = {c.get_name(): c for c in pawn.get_components_by_class(unreal.SceneComponent)}
        R['components'] = sorted(comps)
        rifle, mesh = comps.get('FurinaRifle'), comps.get('FurinaMesh')
        if rifle:
            R['rifle_parent'] = str(rifle.get_attach_parent().get_name()) if rifle.get_attach_parent() else None
            R['rifle_socket'] = str(rifle.get_attach_socket_name())
            R['rifle_visible'] = rifle.is_visible()
            mx = mesh.get_world_transform()
            R['rifle_in_mesh'] = [round(v, 1) for v in mx.inverse_transform_location(rifle.get_world_location()).to_tuple()]
            for b in ('Right-wrist', 'Left-wrist', 'Head', 'Neck'):
                R[b] = [round(v, 1) for v in mx.inverse_transform_location(mesh.get_socket_location(b)).to_tuple()]
        for n in ('FPCamera', 'FollowCamera'):
            if n in comps: R[n + '_active'] = comps[n].is_active()
        if 'FPCamera' in comps:
            R['fpcam_parent'] = str(comps['FPCamera'].get_attach_parent().get_name()); R['fpcam_socket'] = str(comps['FPCamera'].get_attach_socket_name())
        R['curves'] = {c: round(mesh.get_anim_instance().get_curve_value(c), 3) for c in ('AimPitch', 'RifleKick', 'RifleReload')}
        R['control_rot'] = str(pc.get_control_rotation())
    except Exception:
        R['error'] = traceback.format_exc()
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fp_probe.json', 'w'), indent=1, default=str)
    print('FP_PROBE_DONE')
main()
del main
