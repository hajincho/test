import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(['/Game/TFPMovement'],True)
base='/Game/TFPMovement/Demo/Character/Animations/Unarmed/'
R['assets']={}
for n in ['AS_N_Idle','AS_N_Walk_F','AS_N_Run_F','AS_N_Walk_B','Crouch/AS_C_Walk_F','Crouch/AS_C_Idle_Additive','Crouch/AS_N_to_C_Idle']:
 a=unreal.load_asset(base+n);R['assets'][n]={'exists':bool(a)}
 if a:R['assets'][n].update(length=a.get_play_length(),skeleton=str(a.get_editor_property('skeleton')),additive=str(a.get_editor_property('additive_anim_type')))
bs=unreal.load_asset(base+'Crouch/Blendspaces/BS_CrouchMovement_F');R['bs_api']={n:getattr(bs,n).__doc__ for n in dir(bs) if any(k in n for k in ('sample','parameter'))};R['bs_props']={}
for n in ['SampleData','BlendParameters','blend_parameters','sample_data']:
 try:R['bs_props'][n]=str(bs.get_editor_property(n))[:2000]
 except Exception as e:R['bs_props'][n]=str(e)
json.dump(R,open(os.path.join(D,'tfp_source_probe.json'),'w'),indent=1)
