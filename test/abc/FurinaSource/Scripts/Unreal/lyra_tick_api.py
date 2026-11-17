import unreal, json
bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'); cdo = unreal.get_default_object(bp.generated_class())
t = cdo.get_editor_property('primary_actor_tick')
R = {'dir': [n for n in dir(t) if not n.startswith('_')], 'export': t.export_text() if hasattr(t, 'export_text') else None}
try: R['to_dict'] = str(t.to_dict())
except Exception as e: R['to_dict_err'] = str(e)[:100]
R['actor_dir_tick'] = [n for n in dir(cdo) if 'tick' in n.lower()]
try: R['actor_tick_enabled'] = cdo.is_actor_tick_enabled()
except Exception as e: R['ate_err'] = str(e)[:80]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_tick_api.json', 'w'), indent=1, default=str)
