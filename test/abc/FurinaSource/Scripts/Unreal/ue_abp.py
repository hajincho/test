import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
OUT = os.path.join(S, "ue_abp.json")
res = {'log': []}
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
try:
    rtg = unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    tgt = unreal.load_asset('/Game/Furina/Retarget/IK_Furina')
    tc = unreal.IKRigController.get_controller(tgt)
    for side in ('Left', 'Right'):
        r = tc.rename_retarget_chain(side + 'Toe', side + 'Foot'); res['log'].append(('rename', side, str(r)))
    eal.save_asset('/Game/Furina/Retarget/IK_Furina')
    rc = unreal.IKRetargeterController.get_controller(rtg)
    rc.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    names = [c[0] for c in [(str(c.get_editor_property('chain_name')),) for c in tc.get_retarget_chains()]]
    m = []
    for n in names:
        try: m.append((n, str(rc.get_source_chain(n))))
        except Exception as e:
            try: m.append((n, str(rc.get_source_chain(n, ''))))
            except Exception as e2: m.append((n, repr(e2)))
    res['mapping'] = m
    try:
        rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    except Exception as e: res['log'].append(repr(e))
    eal.save_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina')
    # anim blueprint for Furina
    p = '/Game/Furina/ABP_Furina'
    if not eal.does_asset_exist(p):
        f = unreal.AnimBlueprintFactory()
        f.set_editor_property('target_skeleton', unreal.load_asset('/Game/Furina/SK_Furina').get_editor_property('skeleton'))
        f.set_editor_property('preview_skeletal_mesh', unreal.load_asset('/Game/Furina/SK_Furina'))
        abp = tools.create_asset('ABP_Furina', '/Game/Furina', unreal.AnimBlueprint, f)
        eal.save_asset(p)
    abp = unreal.load_asset(p)
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([abp])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('UE_ABP_DONE')
