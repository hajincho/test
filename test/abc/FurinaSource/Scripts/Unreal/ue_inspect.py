import unreal, json, traceback
OUT = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ue_inspect.json"
res = {}
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    res['world'] = world.get_path_name()
    ws = world.get_world_settings()
    gm = ws.get_editor_property('default_game_mode')
    res['world_gamemode'] = gm.get_path_name() if gm else None
    res['project_gamemode'] = unreal.GameMapsSettings.get_default_object().get_editor_property('global_default_game_mode').__str__() if hasattr(unreal, 'GameMapsSettings') else None
    root = '/Game/3DPlatformerGameBundle'
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    bps = []
    for a in ar.get_assets_by_path(root, recursive=True):
        cls = str(a.asset_class_path.asset_name)
        if cls in ('Blueprint', 'AnimBlueprint', 'IKRigDefinition', 'IKRetargeter', 'Skeleton', 'SkeletalMesh', 'BlendSpace', 'BlendSpace1D', 'AnimSequence', 'AnimMontage', 'PhysicsAsset', 'ControlRigBlueprint', 'World'):
            bps.append((cls, str(a.package_name)))
    res['assets'] = bps
    # characters: find blueprints whose generated class is a Character
    chars = []
    for cls, pkg in bps:
        if cls != 'Blueprint': continue
        bp = unreal.load_asset(pkg)
        gen = unreal.BlueprintEditorLibrary.generated_class(bp) if hasattr(unreal, 'BlueprintEditorLibrary') else None
        if gen is None: continue
        cdo = unreal.get_default_object(gen)
        if isinstance(cdo, unreal.Character):
            m = cdo.get_editor_property('mesh')
            chars.append(dict(bp=pkg, parent=str(unreal.BlueprintEditorLibrary.get_parent_class(bp).get_name()) if hasattr(unreal.BlueprintEditorLibrary, 'get_parent_class') else None,
                              mesh=m.get_skinned_asset().get_path_name() if m.get_skinned_asset() else None,
                              anim=str(m.get_editor_property('anim_class').get_path_name()) if m.get_editor_property('anim_class') else None,
                              rel_loc=str(m.get_editor_property('relative_location')), rel_rot=str(m.get_editor_property('relative_rotation')),
                              capsule_hh=cdo.get_editor_property('capsule_component').get_unscaled_capsule_half_height()))
        elif isinstance(cdo, unreal.GameModeBase):
            dp = cdo.get_editor_property('default_pawn_class')
            chars.append(dict(gamemode=pkg, pawn=dp.get_path_name() if dp else None))
    res['chars'] = chars
    # level actors that are characters
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    res['level_chars'] = [(a.get_name(), a.get_class().get_path_name(), str(a.get_editor_property('auto_possess_player'))) for a in acts if isinstance(a, unreal.Pawn)]
    res['level_gm_actors'] = [(a.get_name(), a.get_class().get_path_name()) for a in acts if 'PlayerStart' in a.get_class().get_name()]
    sk = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Meshes/Manny_Simple_SK')
    ref = sk.get_editor_property('skeleton')
    res['manny_skeleton'] = ref.get_path_name()
    res['ikrig_api'] = [n for n in dir(unreal) if 'IKRig' in n or 'Retarget' in n][:80]
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('UE_INSPECT_DONE')
