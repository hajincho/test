import unreal, json, os
S = r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data"
sk = unreal.load_asset('/Game/Furina/SK_Furina')
pose = sk.get_editor_property('skeleton').get_reference_pose()
out = {}
for n in unreal.AnimPoseExtensions.get_bone_names(pose):
    t = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.LOCAL)
    q = t.rotation; p = t.translation; s = t.scale3d
    out[str(n)] = dict(q=[q.x, q.y, q.z, q.w], p=[p.x, p.y, p.z], s=[s.x, s.y, s.z], parent=str(unreal.AnimPoseExtensions.get_parent_bone_name(pose, n)) if hasattr(unreal.AnimPoseExtensions, 'get_parent_bone_name') else None)
json.dump(out, open(os.path.join(S, 'ue_ref.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('REFDUMP_DONE')
