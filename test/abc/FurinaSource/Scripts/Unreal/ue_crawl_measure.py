"""Editor: samples a retargeted crawl clip (default AS_Furina_Crawl_Prone_Fwd_Loop_L) at 30 Hz in component space and reports Hips / feet / hands (position, cm) so the crawl stride can be estimated:
foot contact = the lowest part of the foot height cycle; its backward travel per second = the speed the character must move for no foot sliding.
-> Data/crawl_measure_<clip>.json. usage: py ue_crawl_measure.py [clip_name]"""
import unreal, json, sys, traceback, math
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
CLIP = sys.argv[1] if len(sys.argv) > 1 else 'AS_Furina_Crawl_Prone_Fwd_Loop_L'
BONES = ['Hips', 'Head', 'Left-wrist', 'Right-wrist', 'Left-toe', 'Right-toe', 'Left-knee', 'Right-knee']
def main():
    seq = unreal.load_asset('/Game/Furina/Crawl/' + CLIP); length = seq.get_editor_property('sequence_length'); R = dict(clip=CLIP, length=length, rows=[])
    opts = unreal.AnimPoseEvaluationOptions()
    try: opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
    except Exception:
        try: opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.SOURCE)
        except Exception: pass
    n = int(round(length * 30)) + 1
    for i in range(n):
        t = min(length, i / 30.0); pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, opts)
        row = [round(t, 3)]
        for b in BONES:
            tr = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD); l = tr.translation; row.append([round(l.x, 1), round(l.y, 1), round(l.z, 1)])
        R['rows'].append(row)
    R['bones'] = BONES
    json.dump(R, open(D + r'\crawl_measure_%s.json' % CLIP, 'w')); print('CRAWL_MEASURE', CLIP, n)
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\crawl_measure_%s.json' % CLIP, 'w'), indent=1)
