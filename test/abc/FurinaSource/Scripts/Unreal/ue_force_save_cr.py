"""Force-saves assets (only_if_is_dirty=False) and reports the return values -> Data/force_save_cr.json.
usage: py ue_force_save_cr.py [asset_path ...]   (default: the Control Rig, its skeleton, ABP_Furina and the character BP)"""
import unreal, json, sys
eal = unreal.EditorAssetLibrary
paths = sys.argv[1:] or ['/Game/Furina/CR_FurinaSecondary', '/Game/Furina/SK_Furina_Skeleton', '/Game/Furina/ABP_Furina',
                         '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP']
R = {}
for p in paths:
    a = unreal.load_asset(p)
    R[p] = dict(save_loaded=eal.save_loaded_asset(a, False), save_asset=eal.save_asset(p, False))
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\force_save_cr.json', 'w'), indent=1); print('FORCE_SAVE', R)
