"""First/third-person rifle setup on ThirdPersonCharacter_BP (graph logic is pasted from gen_fp_bp_t3d.py afterwards):
 - inputs: IA_FurinaView (V), IA_FurinaFire (Left mouse), IA_FurinaReload (R) in Default_IMC
 - components under FurinaMesh: FurinaRifle (SK_AssaultRifle, attached to Right-wrist at runtime), FPCamera (Head)
 - curves RifleKick / RifleReload on the Furina fire / reload motions, montages AM_Furina_FP_Fire / _Reload
 - BP_FurinaHUD (crosshair)
Writes Data/fp_character.json."""
import unreal, json, os, traceback
def main():
    D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
    FR = json.load(open(os.path.join(D, 'fp_rig.json')))
    R = {'log': []}
    def log(*a): R['log'].append(' '.join(str(x) for x in a))
    eal = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        # ---- inputs
        imcp = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'
        imc = unreal.load_asset(imcp)
        def listing(): return [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None)
                               for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings')]
        for name, key in (('IA_FurinaView', 'V'), ('IA_FurinaFire', 'LeftMouseButton'), ('IA_FurinaReload', 'R')):
            p = '/Game/Furina/Input/' + name
            ia = unreal.load_asset(p) if eal.does_asset_exist(p) else tools.create_asset(name, '/Game/Furina/Input', unreal.InputAction, None)
            ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
            eal.save_loaded_asset(ia, False)
            if (key, name) not in listing():
                k = unreal.Key(); k.set_editor_property('key_name', key); imc.map_key(ia, k)
        eal.save_loaded_asset(imc, False)
        R['mappings'] = [m for m in listing() if m[1] and ('Furina' in m[1] or m[0] in ('V', 'R', 'LeftMouseButton'))]
        # ---- curves + montages
        A = '/Game/Furina/FP/Anim/'
        for seq_name, curve, times, vals in (('AS_Furina_FP_Fire', 'RifleKick', [0.0, 0.03, 0.15, 0.3], [0.0, 1.0, 0.3, 0.0]),
                                             ('AS_Furina_FP_Reload', 'RifleReload', [0.0, 0.35, 2.6, 3.0], [0.0, 1.0, 1.0, 0.0])):
            seq = unreal.load_asset(A + seq_name)
            if curve not in [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]:
                unreal.AnimationLibrary.add_curve(seq, curve, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
                unreal.AnimationLibrary.add_float_curve_keys(seq, curve, times, vals)
            eal.save_loaded_asset(seq, False)
            mname = seq_name.replace('AS_', 'AM_')
            if not eal.does_asset_exist(A + mname):
                f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', seq)
                tools.create_asset(mname, A[:-1], unreal.AnimMontage, f)
                eal.save_asset(A + mname)
            # montage playback reads the montage's own curves, so the montage carries the same curve
            mon = unreal.load_asset(A + mname)
            if curve not in [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(mon, unreal.RawCurveTrackTypes.RCT_FLOAT)]:
                unreal.AnimationLibrary.add_curve(mon, curve, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
                unreal.AnimationLibrary.add_float_curve_keys(mon, curve, times, vals)
            if 'Fire' in mname:   # recoil must not be swallowed by the default 0.25 s blend-in
                for prop, tm in (('blend_in', 0.04), ('blend_out', 0.12)):
                    ab = mon.get_editor_property(prop); ab.set_editor_property('blend_time', tm); mon.set_editor_property(prop, ab)
            eal.save_loaded_asset(mon, False)
            log('montage', mname, [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(mon, unreal.RawCurveTrackTypes.RCT_FLOAT)])
            del mon
        # ---- HUD
        hp = '/Game/Furina/FP/BP_FurinaHUD'
        if not eal.does_asset_exist(hp):
            f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.HUD)
            tools.create_asset('BP_FurinaHUD', '/Game/Furina/FP', unreal.Blueprint, f)
            eal.save_asset(hp)
        # ---- character components
        bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        lib = unreal.SubobjectDataBlueprintFunctionLibrary
        def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
        hs = handles()
        parent = hs['FurinaMesh']
        def ensure(name, cls):
            h = handles().get(name)
            if h is None:
                h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
                sub.rename_subobject(h, unreal.Text(name)); log('added', name, fail)
            return lib.get_object(lib.get_data(h))
        rifle = ensure('FurinaRifle', unreal.SkeletalMeshComponent)
        rifle.set_editor_property('skeletal_mesh_asset', unreal.load_asset('/Game/Furina/FP/Weapon/SK_AssaultRifle'))
        q = FR['gun_in_rw_q']
        rifle.set_editor_property('relative_location', unreal.Vector(*FR['gun_in_rw_t']))
        rifle.set_editor_property('relative_rotation', unreal.Quat(q[0], q[1], q[2], q[3]).rotator())
        rifle.set_editor_property('relative_scale3d', unreal.Vector(FR['scale'], FR['scale'], FR['scale']))
        try: rifle.set_collision_profile_name('NoCollision')
        except Exception as e: log('rifle collision', repr(e))
        cam = ensure('FPCamera', unreal.CameraComponent)
        cam.set_editor_property('relative_location', unreal.Vector(*FR['cam_head_local']))
        cam.set_editor_property('use_pawn_control_rotation', True)
        cam.set_editor_property('auto_activate', False)
        cam.set_editor_property('field_of_view', 85.0)
        # view state needs no variable: V uses a FlipFlop, fire checks FPCamera.IsActive()
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        R['status'] = str(bp.get_editor_property('status'))
        R['saved'] = eal.save_loaded_asset(bp, False)
        R['components'] = sorted(handles().keys())
        del rifle, cam, parent, hs, bp
        R['ok'] = True
    except Exception:
        R['error'] = traceback.format_exc()
    json.dump(R, open(os.path.join(D, 'fp_character.json'), 'w'), indent=1, default=str)
    print('FP_CHARACTER', R.get('ok'))
main()
del main
