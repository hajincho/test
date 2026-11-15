import unreal,json,os
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={'saved':[],'failed':[]}
paths=['/Game/Furina/CR_FurinaSecondary','/Game/Furina/ABP_Furina','/Game/Furina/SK_Furina_Skeleton','/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP','/Game/Furina/FP/BP_FurinaHUD','/Game/Furina/FP/BP_FurinaBullet','/Game/Furina/M4/BP_223Case','/Game/Furina/M4/M_Brass','/Game/Furina/Input/IA_FurinaCrouch','/Game/Furina/Input/IMC_FurinaStance']
for p in paths:
 a=unreal.load_asset(p)
 if unreal.EditorAssetLibrary.save_loaded_asset(a,False):R['saved'].append(p)
 else:R['failed'].append(p)
R['ok']=not R['failed'];json.dump(R,open(os.path.join(D,'tfp_save.json'),'w'),indent=1)
