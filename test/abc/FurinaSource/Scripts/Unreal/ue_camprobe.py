import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for path in ['/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP']:
        bp = unreal.load_asset(path)
        comps = []
        for h in sub.k2_gather_subobject_data_for_blueprint(bp):
            d = lib.get_data(h); o = lib.get_object(d)
            row = [str(lib.get_variable_name(d)), o.get_class().get_name() if o else None]
            if o and isinstance(o, unreal.SpringArmComponent):
                row += [o.get_editor_property('target_arm_length'), o.get_editor_property('use_pawn_control_rotation'), o.get_editor_property('enable_camera_lag')]
            comps.append(row)
        res['comps'] = comps
        res['graphs'] = [g.get_name() for g in unreal.BlueprintEditorLibrary.find_event_graph(bp).get_outer().get_editor_property('ubergraph_pages')] if False else None
    imc = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC')
    maps = imc.get_editor_property('default_key_mappings') if hasattr(imc, 'default_key_mappings') else None
    try:
        ms = imc.get_editor_property('mappings')
    except Exception:
        ms = maps.get_editor_property('mappings') if maps else []
    res['mappings'] = [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in ms]
    res['imc_props'] = [p for p in dir(imc) if 'map' in p.lower()]
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_camprobe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('CAMPROBE_DONE')
