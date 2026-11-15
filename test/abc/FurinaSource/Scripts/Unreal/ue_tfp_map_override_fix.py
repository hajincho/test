"""Repair level-instance movement overrides that disable the Blueprint's crouch support."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'actors':[]}
try:
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();assert world and world.get_name()=='ExampleLevel'
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if not isinstance(a,unreal.Character) or not a.get_class().get_name().startswith('ThirdPersonCharacter_BP'):continue
  a.modify();cm=a.character_movement;cm.modify();props=cm.get_editor_property('nav_agent_props');before=props.get_editor_property('can_crouch');props.set_editor_property('can_crouch',True);cm.set_editor_property('nav_agent_props',props);cm.set_editor_property('crouched_half_height',58.);cm.set_editor_property('max_walk_speed_crouched',90.);cm.set_editor_property('can_walk_off_ledges_when_crouching',True);R['actors'].append({'name':a.get_name(),'before':before,'after':cm.get_editor_property('nav_agent_props').get_editor_property('can_crouch')})
 R['ok']=bool(R['actors']) and unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/3DPlatformerGameBundle/Levels/ExampleLevel')
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_map_override_fix.json'),'w'),indent=1)
