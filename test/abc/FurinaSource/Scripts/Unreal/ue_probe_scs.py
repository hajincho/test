"""Probe: can Python reach the character BP's SimpleConstructionScript nodes (attach socket, templates)?"""
import unreal, json, os, traceback
def main():
    R = {}
    try:
        bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
        try:
            scs = bp.get_editor_property('simple_construction_script')
            R['scs'] = str(scs)
            nodes = scs.get_all_nodes()
            R['nodes'] = []
            for n in nodes:
                d = {'name': str(n.get_variable_name()) if hasattr(n, 'get_variable_name') else str(n)}
                for prop in ('attach_to_name', 'parent_component_or_variable_name', 'component_class'):
                    try: d[prop] = str(n.get_editor_property(prop))
                    except Exception as e: d[prop] = 'ERR ' + repr(e)[:80]
                R['nodes'].append(d)
            R['scs_node_api'] = [m for m in dir(nodes[0]) if not m.startswith('_')][:80] if nodes else None
        except Exception as e:
            R['scs_err'] = repr(e)
        R['sds_api'] = [m for m in dir(unreal.SubobjectDataSubsystem) if not m.startswith('_')]
        R['sdl_api'] = [m for m in dir(unreal.SubobjectDataBlueprintFunctionLibrary) if not m.startswith('_')]
        R['graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)] if hasattr(unreal.BlueprintEditorLibrary, 'list_graph_names') else None
        R['vars'] = [str(v) for v in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]
    except Exception:
        R['error'] = traceback.format_exc()
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ue_probe_scs.json', 'w'), indent=1, default=str)
    print('PROBE_SCS_DONE')
main()
del main
