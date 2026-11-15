"""Editor: sets the level instance's FurinaMesh asset to SK_Saori and logs what it reads back after 0.2 s, after rerun_construction_scripts, and after save_current_level (what resets it?)
-> Data/mesh_persist.json"""
import unreal, json, time, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
S = {'t0': time.time(), 'log': [], 'step': 0}
def nm(a): return a.get_path_name() if a else None
def inst():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    return unreal.GameplayStatics.get_all_actors_of_class(w, bp.generated_class())[0]
def tick(dt):
    t = time.time() - S['t0']
    try:
        a = inst(); c = a.get_editor_property('FurinaMesh')
        if S['step'] == 0:
            c.set_skinned_asset_and_update(unreal.load_asset('/Game/Saori/SK_Saori')); S['log'].append(('set', nm(c.get_editor_property('skinned_asset')))); S['step'] = 1
        elif S['step'] == 1 and t > 0.5: S['log'].append(('after 0.5s', nm(c.get_editor_property('skinned_asset')))); a.rerun_construction_scripts(); S['log'].append(('after rerun_construction', nm(a.get_editor_property('FurinaMesh').get_editor_property('skinned_asset')))); S['step'] = 2
        elif S['step'] == 2 and t > 1.5:
            S['log'].append(('after 1.5s', nm(inst().get_editor_property('FurinaMesh').get_editor_property('skinned_asset')))); S['log'].append(('save', unreal.EditorLevelLibrary.save_current_level())); S['step'] = 3
        elif S['step'] == 3 and t > 3.5:
            S['log'].append(('after save 3.5s', nm(inst().get_editor_property('FurinaMesh').get_editor_property('skinned_asset')))); S['step'] = 4
            unreal.unregister_slate_post_tick_callback(S['h']); json.dump(S['log'], open(D + r'\mesh_persist.json', 'w'), indent=1); print('MESH_PERSIST', S['log'])
    except Exception:
        unreal.unregister_slate_post_tick_callback(S['h']); json.dump({'error': traceback.format_exc(), 'log': S['log']}, open(D + r'\mesh_persist.json', 'w'), indent=1)
S['h'] = unreal.register_slate_post_tick_callback(tick)
