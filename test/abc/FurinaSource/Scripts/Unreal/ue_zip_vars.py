"""Editor: member variables (and event / function graph names) of the bundle blueprints that drive zipline / pulley riding, filtered by zip / pulley / up / down / vertical / rope / grab / hang
-> Data/zip_vars.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
PATHS = ['/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP', '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP',
         '/Game/3DPlatformerGameBundle/Blueprints/PlatformerActors/Zipline_BP', '/Game/3DPlatformerGameBundle/Blueprints/GrindRailActors/Pulley_BP',
         '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/Manny_AnimBlueprint']
KEYS = ('zip', 'pulley', 'up', 'down', 'vertical', 'rope', 'grab', 'hang', 'rappel', 'cable', 'slide', 'direction')
def main():
    R = {}
    for p in PATHS:
        a = unreal.load_asset(p)
        if not a: R[p] = 'missing'; continue
        names = [str(n) for n in unreal.BlueprintEditorLibrary.list_member_variable_names(a)]
        R[p] = dict(vars=[n for n in names if any(k in n.lower() for k in KEYS)], all_count=len(names))
        try: R[p]['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(a)]
        except Exception: pass
    json.dump(R, open(D + r'\zip_vars.json', 'w'), indent=1, ensure_ascii=False); print('ZIP_VARS', list(R))
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\zip_vars.json', 'w'))
