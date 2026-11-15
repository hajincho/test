"""Dumps the TFP locomotion blend spaces: samples (animation, x, y), sample rate scale, animation rate_scale / length -> Data/dump_bs.json"""
import unreal, json
def main():
    R = {}
    for path in ('/Game/Furina/TFP/BS_FurinaStanding', '/Game/Furina/TFP/BS_FurinaCrouching'):
        bs = unreal.load_asset(path)
        if bs is None: R[path] = None; continue
        rows = []
        for s in bs.get_editor_property('sample_data'):
            a = s.get_editor_property('animation')
            rows.append(dict(anim=a.get_name() if a else None, v=[round(x, 1) for x in s.get_editor_property('sample_value').to_tuple()[:2]],
                             sample_rate=s.get_editor_property('rate_scale'), anim_rate=a.get_editor_property('rate_scale') if a else None,
                             length=round(a.get_play_length(), 3) if a else None))
        R[path] = dict(axes=[(str(bs.get_editor_property('axis_to_scale_animation'))), ], rows=rows)
        del bs
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\dump_bs.json', 'w'), indent=1, default=str)
    print('DUMP_BS')
main(); del main
