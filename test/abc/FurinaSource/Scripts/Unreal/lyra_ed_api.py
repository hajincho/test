import unreal, json
bp = unreal.load_asset('/ShooterCore/Game/B_Hero_ShooterMannequin')
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
R = {'ed': [n for n in dir(ed) if not n.startswith('_')], 'cls': [n for n in dir(unreal.BlueprintGraphEditor) if not n.startswith('_') and n not in dir(ed)]}
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
R['comps'] = [str(L.get_variable_name(L.get_data(h))) for h in S.k2_gather_subobject_data_for_blueprint(bp)]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_ed_api.json', 'w'), indent=1)
