import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP')
    gen = unreal.BlueprintEditorLibrary.generated_class(bp)
    cdo = unreal.get_default_object(gen)
    for p in dir(cdo):
        if p.startswith('_'): continue
        if any(k in p.lower() for k in ('speed', 'sprint', 'walk', 'run')):
            try: res[p] = str(cdo.get_editor_property(p))
            except Exception as e: res[p] = 'ERR'
    ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    ccdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(ch))
    for c in ccdo.get_components_by_class(unreal.ActorComponent) if hasattr(ccdo, 'get_components_by_class') else []:
        res['comp_' + c.get_name()] = c.get_class().get_name()
    # component template on the character BP (instance values may override)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(ch):
        o = lib.get_object(lib.get_data(h))
        if o and 'Platformer_Component' in o.get_class().get_name():
            for p in dir(o):
                if any(k in p.lower() for k in ('speed', 'sprint', 'walk', 'run')) and not p.startswith('_'):
                    try: res['inst_' + p] = str(o.get_editor_property(p))
                    except Exception: pass
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_speedprobe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('SPEEDPROBE_DONE')
