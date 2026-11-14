"""Lists the member variables (name + type) of the bundle traversal components and the character BP, and the
BlueprintEditorLibrary helpers available for typed variables."""
import unreal, json
def main():
    R = {}
    paths = {'grind': '/Game/3DPlatformerGameBundle/Blueprints/Components/Grind_Rail_Component_BP',
             'homing': '/Game/3DPlatformerGameBundle/Blueprints/Components/Homing_Attack_Component_BP',
             'platformer': '/Game/3DPlatformerGameBundle/Blueprints/Components/Platformer_Component_BP',
             'char': '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'}
    for k, p in paths.items():
        try:
            bp = unreal.load_asset(p)
            if not bp: R[k] = 'missing'; continue
            names = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if '/Script/' not in str(v)]
            out = {}
            for n in names:
                try: out[n] = str(unreal.BlueprintEditorLibrary.get_member_variable_type(bp, n))[:120]
                except Exception as e: out[n] = '?'
            R[k] = out
            R[k + '_graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
            del bp
        except Exception as e:
            R[k] = repr(e)[:200]
    R['bel_type_helpers'] = [m for m in dir(unreal.BlueprintEditorLibrary) if 'type' in m.lower()]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\traversal_probe.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('TRAVERSAL_PROBE_DONE')
main()
del main
