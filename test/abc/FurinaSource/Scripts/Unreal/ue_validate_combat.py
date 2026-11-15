"""Crouch foot contact and M4 stock/hand reach in the actual Control Rig."""
import unreal,json,os,math,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 bp=unreal.load_asset('/Game/Furina/CR_FurinaSecondary');pose=unreal.load_asset('/Game/Furina/SK_Furina_Skeleton').get_reference_pose();names=unreal.AnimPoseExtensions.get_bone_names(pose);rest={str(n):unreal.AnimPoseExtensions.get_bone_pose(pose,n,unreal.AnimPoseSpaces.LOCAL) for n in names}
 def bone(n):return unreal.RigElementKey(type=unreal.RigElementType.BONE,name=n)
 def curve(n):return unreal.RigElementKey(type=unreal.RigElementType.CURVE,name=n)
 rig=bp.create_control_rig();rig.set_delta_time(1/60);rig.execute('Forwards Solve');h=rig.get_hierarchy();initial={n:h.get_global_transform(bone(n)).translation for n in ('Left-ankle','Right-ankle')};rows=[]
 for frame in range(360):
  for n,x in rest.items():h.set_local_transform(bone(n),x,False,True)
  crouch=1. if 60<=frame<240 else 0.
  for name,val in [('FurinaIdle',1.),('FurinaWalk',0.),('Crouch',crouch),('ViewTP',1.),('AimShoulder',1.)]:h.set_curve_value(curve(name),val)
  rig.set_absolute_and_delta_time(frame/60,1/60);assert rig.execute('Forwards Solve')
  if frame in (59,119,179,239,299,359):
   row={'frame':frame,'crouch':crouch,'hips':list(h.get_global_transform(bone('Hips')).translation.to_tuple())}
   row['ankles']={n:list(h.get_global_transform(bone(n)).translation.to_tuple()) for n in initial};row['foot_error_cm']=max((h.get_global_transform(bone(n)).translation-initial[n]).length() for n in initial)
   row['lengths']={s:[(h.get_global_transform(bone(s+'-knee')).translation-h.get_global_transform(bone(s+'-leg')).translation).length(),(h.get_global_transform(bone(s+'-ankle')).translation-h.get_global_transform(bone(s+'-knee')).translation).length()] for s in ('Left','Right')};rows.append(row)
 R['samples']=rows;R['max_settled_foot_error_cm']=max(r['foot_error_cm'] for r in rows);R['ok']=R['max_settled_foot_error_cm']<.5
 R['statuses']={p:str(unreal.load_asset(p).get_editor_property('status')) for p in ['/Game/Furina/CR_FurinaSecondary','/Game/Furina/ABP_Furina','/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP','/Game/Furina/FP/BP_FurinaBullet']}
 R['m4_bounds']=str(unreal.load_asset('/Game/Furina/M4/SK_M4A1').get_bounds())
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'combat_validation.json'),'w'),indent=1)
