"""Direction/speed blend spaces with ground contact-based playback rates on Furina."""
import unreal,os,json,math,statistics,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'rates':{}}
def main():
 T=unreal.AssetToolsHelpers.get_asset_tools();E=unreal.EditorAssetLibrary;A=unreal.AnimPoseExtensions;opts=unreal.AnimPoseEvaluationOptions();W=unreal.AnimPoseSpaces.WORLD;folder='/Game/Furina/TFP/Anim/'
 def load(name):
  a=unreal.load_asset(folder+'AS_Furina_TFP_'+name);assert a,name;return a
 def contact_speed(a):
  name=a.get_name()
  if name in R['rates']:return R['rates'][name]
  length=a.get_play_length();rows=[];N=max(24,round(length*30))
  for k in range(N):
   p=A.get_anim_pose_at_time(a,k*length/N,opts);row={}
   for side in ('Left','Right'):
    ankle=A.get_bone_pose(p,side+'-ankle',W).translation;toe=A.get_bone_pose(p,side+'-toe',W).translation;row[side]=(ankle.x,ankle.y,toe.z)
   rows.append(row)
  speeds=[]
  for side in ('Left','Right'):
   low=min(r[side][2] for r in rows)
   for k in range(1,len(rows)):
    x,y,z=rows[k][side];px,py,pz=rows[k-1][side];v=math.hypot(x-px,y-py)/(length/N)
    if z<low+2.5 and pz<low+2.5 and v>15:speeds.append(v)
  speed=statistics.median(speeds) if speeds else 120.;R['rates'][name]=speed;return speed
 def blend(name,crouch):
  path='/Game/Furina/TFP/'+name
  if E.does_asset_exist(path):b=unreal.load_asset(path)
  else:
   f=unreal.BlendSpaceFactoryNew();f.set_editor_property('target_skeleton',unreal.load_asset('/Game/Furina/SK_Furina_Skeleton'));b=T.create_asset(name,'/Game/Furina/TFP',unreal.BlendSpace,f)
  pars=list(b.get_editor_property('BlendParameters'))
  for i,(label,mi,ma,grid) in enumerate([('Direction',-180,180,8),('Speed',0,360 if crouch else 600,6)]):
   q=pars[i];q.import_text('(DisplayName="%s",Min=%f,Max=%f,GridNum=%d,bSnapToGrid=False,bWrapInput=%s)'%(label,mi,ma,grid,'True' if i==0 else 'False'));pars[i]=q
  b.set_editor_property('BlendParameters',pars)
  idle=load('C_Idle_Additive' if crouch else 'N_Idle');samples=[]
  def sample(a,d,s,rate=1):
   x=unreal.BlendSample();assert x.import_text('(Animation="/Script/Engine.AnimSequence\'%s\'",SampleValue=(X=%f,Y=%f,Z=0),RateScale=%f)'%(a.get_path_name(),d,s,rate));samples.append(x)
  for d in (-180,-135,-90,-45,0,45,90,135,180):sample(idle,d,0)
  for d in (-180,-135,-90,-45,0,45,90,135,180):
   if crouch:
    n='C_Walk_B' if abs(d)>135 else 'C_Walk_F' if abs(d)<45 else 'C_Walk_L' if d<0 else 'C_Walk_R'
    a=load(n);speed=contact_speed(a);sample(a,d,90,90/speed);sample(a,d,360,min(4,360/speed))
   else:
    walk={-180:'N_Walk_B',-135:'N_Walk_BL_135',-90:'N_Walk_FL',-45:'N_Walk_FL_45',0:'N_Walk_F',45:'N_Walk_FR_45',90:'N_Walk_FR',135:'N_Walk_BR_135',180:'N_Walk_B'}[d]
    a=load(walk);sample(a,d,120,120/contact_speed(a))
    run='N_Run_B' if abs(d)>135 else 'N_Run_F' if abs(d)<45 else 'N_Run_FL' if d<0 else 'N_Run_FR';a=load(run);sample(a,d,600,min(2.5,600/contact_speed(a)))
  b.set_editor_property('SampleData',samples);E.save_loaded_asset(b,False);return b
 standing=blend('BS_FurinaStanding',False);crouching=blend('BS_FurinaCrouching',True)
 bp=unreal.load_asset('/Game/Furina/ABP_Furina');ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,'AnimGraph');R['nodes']={}
 for name,asset in [('TFPStanding',standing),('TFPCrouching',crouching)]:
  n=next((n for n in ed.list_all_nodes() if n.get_name()==name),None)
  if not n:n=ed.create_node_from_name('애니메이션|블렌드스페이스|블렌드스페이스플레이어',unreal.Vector2D(0,0),[]);assert n,name;n.rename(name)
  v=n.get_editor_property('node');v.set_editor_property('blend_space',asset);n.set_editor_property('node',v)
  old=n.get_editor_property('initial_update_function').copy();tmp=old.copy();tmp.import_text('(MemberName="FurinaReconstructTemporary")');n.set_editor_property('initial_update_function',tmp);n.set_editor_property('initial_update_function',old)
  R['nodes'][name]=[str(p.get_pin_name()) for p in n.list_all_pins()]
 R['ok']=True
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_blends.json'),'w'),indent=1)
