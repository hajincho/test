"""Editor(테스트용): /Game/Furina/QA/BP_FurinaTestDummy (큐브 메시 + AbilitySystemComponent) 생성 후 현재 레벨 푸리나 앞(-Y 방향 600cm)에 배치. 테스트 후 ue_bullet_hit_dummy_cleanup 로 제거.
usage: py ue_bullet_hit_dummy_setup.py [x y z]  -> Data/bullet_hit_dummy_setup.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bullet_hit_dummy_setup.json'
R = {}
try:
    path = '/Game/Furina/QA/BP_FurinaTestDummy'
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_FurinaTestDummy', '/Game/Furina/QA', None, f)
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
        hs = sub.k2_gather_subobject_data_for_blueprint(bp); root = hs[0]
        h1, err = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)); sub.rename_subobject(h1, unreal.Text('Body'))
        h2, err2 = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.AbilitySystemComponent, blueprint_context=bp)); sub.rename_subobject(h2, unreal.Text('ASC'))
        body = lib.get_object(lib.get_data(h1)); body.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Cube'))
        body.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 6)); body.set_collision_profile_name('BlockAll')
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False); R['created'] = True
    bp = unreal.load_asset(path); gc = bp.generated_class()
    a = [float(x) for x in sys.argv[1:4]] if len(sys.argv) >= 4 else [170.0, -1645.0, 802.0]
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for old in [x for x in eas.get_all_level_actors() if x.get_class() == gc]: eas.destroy_actor(old)
    act = eas.spawn_actor_from_class(gc, unreal.Vector(*a)); act.set_actor_label('FurinaTestDummy'); R['placed'] = str(act.get_actor_location())
    R['level_saved'] = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w'), indent=1, default=str); print('DUMMY_SETUP', R.get('placed'), R.get('error', '')[-300:])
