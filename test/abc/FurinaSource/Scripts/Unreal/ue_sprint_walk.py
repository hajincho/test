"""Shift-only sprint + walk signal:
 - IA_FurinaSprint (bool) mapped to LeftShift in Default_IMC
 - ThirdPersonCharacter_BP default MaxWalkSpeed = 120 (Unity walkSpeed 1.2 m/s)
 - FurinaWalk curve (=1) on Manny's walk anims, so ABP_Furina can blend in the Unity walk motion
 - opens the character BP for pasting gen_sprint_t3d.py output"""
import unreal, json, os, traceback
D = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
res = {'log': []}
def log(*a): res['log'].append(' '.join(str(x) for x in a))
eal = unreal.EditorAssetLibrary
try:
    p = '/Game/Furina/Input/IA_FurinaSprint'
    ia = unreal.load_asset(p) if eal.does_asset_exist(p) else unreal.AssetToolsHelpers.get_asset_tools().create_asset('IA_FurinaSprint', '/Game/Furina/Input', unreal.InputAction, None)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eal.save_loaded_asset(ia, False)
    imcp = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC'
    imc = unreal.load_asset(imcp)
    if not [m for m in imc.get_editor_property('mappings') if m.action == ia]:
        key = unreal.Key(); key.set_editor_property('key_name', 'LeftShift')
        imc.map_key(ia, key)
    eal.save_loaded_asset(imc, False)
    log('mappings', [(str(m.key.get_editor_property('key_name')), m.action.get_name() if m.action else None) for m in imc.get_editor_property('mappings')])
    bpp = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
    bp = unreal.load_asset(bpp)
    cdo = unreal.get_default_object(bp.generated_class())
    cm = cdo.get_editor_property('character_movement')
    log('max_walk_speed before', cm.get_editor_property('max_walk_speed'))
    cm.set_editor_property('max_walk_speed', 120.0)
    log('max_walk_speed after', cm.get_editor_property('max_walk_speed'))
    A = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/'
    for n in ('Walk_Fwd_Anim', 'Walk_InPlace_Anim'):
        a = unreal.load_asset(A + n)
        if 'FurinaWalk' not in [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]:
            unreal.AnimationLibrary.add_curve(a, 'FurinaWalk', unreal.RawCurveTrackTypes.RCT_FLOAT, False)
            unreal.AnimationLibrary.add_float_curve_keys(a, 'FurinaWalk', [0.0, a.get_play_length()], [1.0, 1.0])
        eal.save_asset(A + n)
        log(n, [str(c) for c in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)])
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(os.path.join(D, 'ue_sprint_walk.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('SPRINT_WALK_DONE')
