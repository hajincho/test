"""Editor: samples the bundle's zipline animations (Manny skeleton: pelvis, head, hand_l, hand_r, lowerarm_l/r, upperarm_l/r) at 5 times and reports component-space positions (cm), so the
one-handed / two-handed grips and arm extension can be compared -> Data/zip_anim_measure.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
B = '/Game/3DPlatformerGameBundle/Animations/'
CLIPS = ['One_Handed_Zipline_Anim', 'Two_Handed_Zipline_Anim', 'Zipline_Anim', 'Alt_Animations/Zipline_Anim', 'Alt_Animations/Zipline_Up_1_Anim', 'Alt_Animations/Zipline_Up_2_Anim', 'Alt_Animations/Zipline_Down_1_Anim',
         'Zipline_Up_1_Anim', 'Zipline_Up_2_Anim', 'Zipline_Down_1_Anim']
BONES = ['pelvis', 'spine_05', 'head', 'upperarm_l', 'lowerarm_l', 'hand_l', 'upperarm_r', 'lowerarm_r', 'hand_r']
def main():
    R = {}
    for c in CLIPS:
        a = unreal.load_asset(B + c)
        if not a: R[c] = 'missing'; continue
        L = a.get_editor_property('sequence_length'); rows = []
        opts = unreal.AnimPoseEvaluationOptions()
        for t in (0.0, 0.25 * L, 0.5 * L, 0.75 * L):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts); row = [round(t, 2)]
            for b in BONES:
                try: v = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation; row.append([round(v.x, 1), round(v.y, 1), round(v.z, 1)])
                except Exception as e: row.append(str(e)[:30])
            rows.append(row)
        R[c] = dict(length=round(L, 2), skeleton=str(a.get_editor_property('skeleton').get_name()), rows=rows)
    R['bones'] = BONES
    json.dump(R, open(D + r'\zip_anim_measure.json', 'w'), indent=1); print('ZIP_ANIM', list(R))
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\zip_anim_measure.json', 'w'))
