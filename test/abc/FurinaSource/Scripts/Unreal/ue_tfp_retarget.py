"""Retarget TFP reference animations to Furina without modifying the source project."""
import unreal,json,os,traceback
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data';R={}
def main():
 E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();dest='/Game/Furina/TFP'
 source=unreal.load_asset('/Game/TFPMovement/Demo/Character/Mannequins/Meshes/SKM_Manny_Simple');target=unreal.load_asset('/Game/Furina/SK_Furina')
 p=dest+'/IK_TFPManny';rig=unreal.load_asset(p) if E.does_asset_exist(p) else T.duplicate_asset('IK_TFPManny',dest,unreal.load_asset('/Game/Furina/Retarget/IK_Manny'));unreal.IKRigController.get_controller(rig).set_skeletal_mesh(source);E.save_loaded_asset(rig,False)
 p=dest+'/RTG_TFPToFurina';rtg=unreal.load_asset(p) if E.does_asset_exist(p) else T.duplicate_asset('RTG_TFPToFurina',dest,unreal.load_asset('/Game/Furina/Retarget/RTG_Manny_To_Furina'));c=unreal.IKRetargeterController.get_controller(rtg);c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE,rig);c.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE,source);c.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE,rig);E.save_loaded_asset(rtg,False)
 paths=E.list_assets('/Game/TFPMovement/Demo/Character/Animations',True,False);items=[E.find_asset_data(p) for p in paths if isinstance(unreal.load_asset(p),(unreal.AnimSequence,unreal.BlendSpace))]
 out=unreal.IKRetargetBatchOperation.duplicate_and_retarget(items,source,target,rtg,search='AS_',replace='AS_Furina_TFP_',target_path=dest+'/Anim',use_source_path=False,include_referenced_assets=True,overwrite_existing_files=True)
 R['count']=len(out);R['assets']=[str(x.package_name) for x in out]
 for a in out:E.save_asset(str(a.package_name))
 R['ok']=len(out)>20
try:main()
except Exception:R['error']=traceback.format_exc()
json.dump(R,open(os.path.join(D,'tfp_retarget.json'),'w'),indent=1)
