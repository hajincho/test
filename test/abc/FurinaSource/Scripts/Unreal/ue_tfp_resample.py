import unreal,json,os,time
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';paths=['/Game/Furina/TFP/BS_FurinaStanding','/Game/Furina/TFP/BS_FurinaCrouching'];assets=[unreal.load_asset(p) for p in paths];sub=unreal.get_editor_subsystem(unreal.AssetEditorSubsystem);R={'opened':sub.open_editor_for_assets(assets)};S={'start':time.monotonic()}
def tick(dt):
 if time.monotonic()-S['start']<2:return
 unreal.unregister_slate_post_tick_callback(S['h']);R['saved']=[unreal.EditorAssetLibrary.save_loaded_asset(a,False) for a in assets];json.dump(R,open(os.path.join(D,'tfp_resample.json'),'w'),indent=1)
S['h']=unreal.register_slate_post_tick_callback(tick)
