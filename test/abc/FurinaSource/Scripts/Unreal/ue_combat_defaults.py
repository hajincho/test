import unreal,json
b=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP');c=unreal.get_default_object(b.generated_class());m=c.character_movement
R={'nav':str(m.get_editor_property('nav_agent_props')),'crouched_height':m.get_editor_property('crouched_half_height'),'ammo':c.get_editor_property('FurinaAmmo')};json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\combat_defaults.json','w'),indent=1)
