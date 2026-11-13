import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
OUT = os.path.join(S, "ue_character.json")
BPS = ['/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP',
       '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/GrindRailCharacterBP/Ver_2_ThirdPersonCharacter_BP',
       '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/HomingAttackCharacterBP/ThirdPersonCharacter_BP',
       '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/JumpPadCharacterBP/ThirdPersonCharacter_BP']
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
try:
    unreal.EditorAssetLibrary.save_asset('/Game/Furina/ABP_Furina')
    sk = unreal.load_asset('/Game/Furina/SK_Furina')
    abp = unreal.load_asset('/Game/Furina/ABP_Furina')
    abp_class = unreal.load_object(None, '/Game/Furina/ABP_Furina.ABP_Furina_C')
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for path in BPS:
        bp = unreal.load_asset(path)
        handles = sub.k2_gather_subobject_data_for_blueprint(bp)
        mesh_h, existing = None, None
        for h in handles:
            d = lib.get_data(h)
            name = str(lib.get_variable_name(d))
            if name == 'Mesh' or name == 'CharacterMesh0': mesh_h = h
            if name == 'FurinaMesh': existing = h
        if mesh_h is None:
            log(path, 'no Mesh handle', [str(lib.get_variable_name(lib.get_data(h))) for h in handles]); continue
        if existing is None:
            params = unreal.AddNewSubobjectParams(parent_handle=mesh_h, new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)
            existing, fail = sub.add_new_subobject(params)
            log(path, 'added', fail)
            sub.rename_subobject(existing, unreal.Text('FurinaMesh'))
        comp = lib.get_object(lib.get_data(existing))
        comp.set_editor_property('skeletal_mesh_asset', sk)
        comp.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
        comp.set_editor_property('anim_class', abp_class)
        comp.set_editor_property('relative_location', unreal.Vector(0, 0, 0))
        comp.set_editor_property('relative_rotation', unreal.Rotator(0, 0, 0))
        try: comp.set_collision_profile_name('NoCollision')
        except Exception as e: log('collision', repr(e))
        # Manny keeps driving every animation (montages, layers, components) but is not rendered.
        gen = unreal.BlueprintEditorLibrary.generated_class(bp)
        cdo = unreal.get_default_object(gen)
        manny = cdo.get_editor_property('mesh')
        manny.set_editor_property('visible', False)
        manny.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        mh = lib.get_object(lib.get_data(mesh_h))
        if mh and mh != manny:
            mh.set_editor_property('visible', False)
            mh.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        eal.save_asset(path)
        log(path, 'ok', comp.get_path_name())
    # verify on the placed player in the open level
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for a in acts:
        if isinstance(a, unreal.Character):
            comps = a.get_components_by_class(unreal.SkeletalMeshComponent)
            res['level_player'] = [(c.get_name(), c.get_skinned_asset().get_name() if c.get_skinned_asset() else None, c.is_visible(), str(c.get_editor_property('anim_class'))) for c in comps]
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('UE_CHARACTER_DONE')
