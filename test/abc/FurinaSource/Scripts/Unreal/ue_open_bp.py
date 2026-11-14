"""Opens a blueprint editor. usage: py ue_open_bp.py <asset path> ; or 'compile <asset path>' to compile + save (results to Data/bp_compile.json)."""
import unreal, sys, json
def main():
    args = sys.argv[1:]
    if args and args[0] == 'compile':
        bp = unreal.load_asset(args[1])
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        st = bp.get_editor_property('status')
        saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if st != unreal.BlueprintStatus.BS_ERROR else False
        json.dump({'asset': args[1], 'status': str(st), 'saved': saved}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bp_compile.json', 'w'))
        print('BP_COMPILE', st, saved)
        del bp
    else:
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([unreal.load_asset(args[0])])
main()
del main
