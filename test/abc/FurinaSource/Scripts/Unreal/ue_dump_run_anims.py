"""Dumps the run-related blend space samples: Furina TFP BS_FurinaStanding and the bundle's Manny WalkRun_BlendSpace (source of the original run footstep sounds):
sample position, animation, length, rate_scale, notifies -> Data/run_anims.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def dump(path):
    bs = unreal.load_asset(path); out = []
    for s in bs.get_editor_property('sample_data'):
        a = s.get_editor_property('animation'); v = s.get_editor_property('sample_value')
        row = dict(pos=[round(v.x, 1), round(v.y, 1)], rate=round(s.get_editor_property('rate_scale'), 3), anim=a.get_name() if a else None)
        if a:
            row['len'] = round(a.get_editor_property('sequence_length'), 3)
            try: row['notifies'] = [(str(n.get_editor_property('notify_name')), round(n.get_editor_property('trigger_time_offset') + n.get_editor_property('display_time') if hasattr(n, 'display_time') else 0, 3)) for n in a.get_editor_property('notifies')][:8]
            except Exception as e: row['notifies'] = 'ERR ' + str(e)[:60]
        out.append(row)
    return out
try:
    R = dict(furina=dump('/Game/Furina/TFP/BS_FurinaStanding'),
             manny=dump('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/WalkRun_BlendSpace'))
except Exception: R = dict(error=traceback.format_exc())
json.dump(R, open(D + r'\run_anims.json', 'w'), indent=1); print('RUN_ANIMS', R.get('error', 'ok')[:300])
