"""헤드리스(읽기 전용, 저장 안 함): 뷰모델 스켈레탈의 참조 포즈에서 VM_* 뼈 컴포넌트 공간 변환 + 낱발 탄 스태틱 메시 경계 -> Data/fpvm_refpose.json"""
import unreal, json, traceback
R = {}
def cs(comp, name):
    T = None; b = name
    while b and str(b) != 'None':
        i = comp.get_bone_index(b); t = comp.get_ref_pose_transform(i)
        T = t if T is None else T * t if False else unreal.MathLibrary.compose_transforms(T, t)
        b = comp.get_parent_bone(b)
    return T
try:
    for key in ('Kar98k', 'G43', 'P38', 'P08', 'PP'):
        p = '/Game/Furina/FPVM/%s/SK_FPVM_%s' % (key, key); sm = unreal.load_asset(p)
        if not sm: R[key] = 'missing'; continue
        comp = unreal.new_object(unreal.SkeletalMeshComponent); comp.set_skeletal_mesh_asset(sm); out = {}
        for b in ('VM_Gun', 'VM_Clip', 'VM_Rounds', 'VM_Bolt', 'VM_Carrier', 'VM_Exterior'):
            if comp.get_bone_index(b) < 0: continue
            T = cs(comp, b); q = T.rotation; l = T.translation; s = T.scale3d
            out[b] = {'loc': [l.x, l.y, l.z], 'quat': [q.x, q.y, q.z, q.w], 'scale': [s.x, s.y, s.z]}
        out['bones'] = comp.get_num_bones(); R[key] = out
    sm = unreal.load_asset('/Game/Furina/FPVM/SM_FPVM_LooseRound')
    if sm: b = sm.get_bounding_box(); R['loose_round_bounds'] = [[b.min.x, b.min.y, b.min.z], [b.max.x, b.max.y, b.max.z]]
except Exception: R['error'] = traceback.format_exc()[-1000:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\fpvm_refpose.json', 'w'), indent=1); print('REFPOSE done')
