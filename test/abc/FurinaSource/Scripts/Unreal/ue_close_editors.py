"""Closes every open asset editor (assets are saved separately); used when an asset editor window covers the level editor."""
import unreal
def main():
    sub = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
    for p in ('/Game/Furina/ABP_Furina', '/Game/Furina/CR_FurinaSecondary', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP', '/Game/Furina/FP/BP_FurinaHUD'):
        a = unreal.load_asset(p)
        if a: sub.close_all_editors_for_asset(a)
    print('CLOSED_ASSET_EDITORS')
main()
del main
