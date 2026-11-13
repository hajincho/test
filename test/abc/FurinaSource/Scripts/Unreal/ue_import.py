import unreal, json, traceback, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
TEX = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Textures"
OUT = os.path.join(S, "ue_import.json")
DEST = "/Game/Furina"
res = {}
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def run_task(filename, dest, options=None, name=None):
    t = unreal.AssetImportTask()
    t.filename = filename; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    if name: t.destination_name = name
    if options: t.options = options
    tools.import_asset_tasks([t])
    return list(t.imported_object_paths)

try:
    # --- skeletal mesh
    if not eal.does_asset_exist(DEST + "/SK_Furina"):
        ui = unreal.FbxImportUI()
        ui.import_mesh = True; ui.import_as_skeletal = True
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        ui.import_materials = False; ui.import_textures = False; ui.import_animations = False
        ui.create_physics_asset = False
        ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
        res['mesh_import'] = run_task(os.path.join(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\Variants', 'Furina_UE.fbx'), DEST, ui, "SK_Furina")
    # --- textures
    texs = {}
    for n in ["Face", "HairDetail", "HairSheen", "Outfit", "SkinHair"]:
        p = DEST + "/Textures/T_Furina_" + n
        if not eal.does_asset_exist(p):
            run_task(os.path.join(TEX, n + ".png"), DEST + "/Textures", None, "T_Furina_" + n)
        texs[n] = unreal.load_asset(p)
    # --- master materials
    def master(name, translucent):
        path = DEST + "/Materials/" + name
        if eal.does_asset_exist(path): return unreal.load_asset(path)
        m = tools.create_asset(name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property('two_sided', True)
        if translucent:
            m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        else:
            m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
            m.set_editor_property('opacity_mask_clip_value', 0.3)
        tex = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
        tex.set_editor_property('parameter_name', 'BaseTex')
        tex.set_editor_property('texture', texs['Outfit'])
        mel.connect_material_property(tex, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(tex, 'A', unreal.MaterialProperty.MP_OPACITY if translucent else unreal.MaterialProperty.MP_OPACITY_MASK)
        rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 300)
        rough.set_editor_property('r', 0.77)  # Unity smoothness 0.23
        mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        spec = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 400)
        spec.set_editor_property('r', 0.3)
        mel.connect_material_property(spec, '', unreal.MaterialProperty.MP_SPECULAR)
        mel.recompile_material(m)
        eal.save_asset(path)
        return m
    m_op = master("M_Furina_Opaque", False)
    m_tr = master("M_Furina_Translucent", True)
    sk = unreal.load_asset(DEST + "/SK_Furina")
    mats = sk.get_editor_property('materials')
    res['slots'] = [str(m.material_slot_name) for m in mats]
    new = []
    for sm in mats:
        slot = str(sm.material_slot_name)
        key = slot.replace('Furina_', '')
        path = DEST + "/Materials/MI_" + slot
        if eal.does_asset_exist(path):
            mi = unreal.load_asset(path)
        else:
            mi = tools.create_asset("MI_" + slot, DEST + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mel.set_material_instance_parent(mi, m_tr if key == 'HairSheen' else m_op)
            if key in texs: mel.set_material_instance_texture_parameter_value(mi, 'BaseTex', texs[key])
            eal.save_asset(path)
        sm.set_editor_property('material_interface', mi)
        new.append(sm)
    sk.set_editor_property('materials', new)
    eal.save_asset(DEST + "/SK_Furina")
    skel = sk.get_editor_property('skeleton')
    res['skeleton'] = skel.get_path_name()
    # bone positions (component space of the ref pose)
    names = [str(n) for n in sk.get_editor_property('skeleton').get_editor_property('bone_tree')] if False else None
    lib = unreal.AnimationLibrary if hasattr(unreal, 'AnimationLibrary') else None
    ref = {}
    for b in ['Hips', 'Head', 'Left ankle', 'Left toe', 'Left leg', 'Left wrist', 'Right wrist', 'HB1_1_0']:
        try:
            t = unreal.AnimationLibrary.get_bone_pose_for_frame if False else None
        except Exception: pass
    res['bounds'] = str(sk.get_bounds())
    res['probe'] = dict(
        physasset_props=[p for p in dir(unreal.PhysicsAsset) if not p.startswith('_')][:200],
        anim_nodes=[n for n in dir(unreal) if n.startswith('AnimGraphNode_') and any(k in n for k in ('Dynamics', 'RigidBody', 'Retarget', 'LocalToComponent', 'ComponentToLocal', 'SpringBone'))],
        abp_factory=hasattr(unreal, 'AnimBlueprintFactory'),
        ikrig=[n for n in dir(unreal) if n in ('IKRigController', 'IKRetargeterController', 'IKRigDefinitionFactory', 'IKRetargetFactory')],
        sk_props=[p for p in dir(sk) if 'post' in p.lower() or 'physics' in p.lower()],
        pae=[n for n in dir(unreal) if 'PhysicsAsset' in n])
except Exception:
    res['error'] = traceback.format_exc()
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('UE_IMPORT_DONE')

