"""Stride warp, animation side (2026-11-15): raises the sample rates of the standing walk (120 cm/s) and run (600 cm/s) samples of
BS_FurinaStanding by 1/s (walk s = 0.72, run s = 0.92) so a planted foot keeps moving with the ground while the Control Rig pulls the
foot targets toward the pelvis by (1 - s) (ue_build_cr.py: StrideD). Base rates are kept in Data/tfp_stride_base.json, so re-running is
idempotent. usage: py ue_tfp_stride.py [walk_s run_s [run_cadence]]   (1 1 restores the base rates)
run_cadence = run steps per second (2026-11-15): when given, every run sample (one cycle = 2 steps) plays at rate = anim length * run_cadence / 2 instead of base / run_s.
The base run cycle gave 4.5-5 steps/s while the bundle's run footstep sounds (Run_Fwd_Anim: 6 'Footstep' notifies in 1.9 s) are 3.2 steps/s; 3.5 keeps the feet near the sound.
The planted foot then slips a little against the 600 cm/s ground speed."""
import unreal, json, os, sys
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    ws = float(sys.argv[1]) if len(sys.argv) > 1 else 0.72
    rs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.92
    cad = float(sys.argv[3]) if len(sys.argv) > 3 else None
    bs = unreal.load_asset('/Game/Furina/TFP/BS_FurinaStanding')
    path = os.path.join(D, 'tfp_stride_base.json')
    base = json.load(open(path)) if os.path.exists(path) else None
    samples = list(bs.get_editor_property('sample_data'))
    if base is None:
        base = [s.get_editor_property('rate_scale') for s in samples]; json.dump(base, open(path, 'w'))
    out = []
    for i, s in enumerate(samples):
        y = s.get_editor_property('sample_value').y
        k = 1.0 / ws if abs(y - 120) < 1 else ((1.0 / rs) if abs(y - 600) < 1 else 1.0)
        if cad and abs(y - 600) < 1 and s.get_editor_property('animation'): k = s.get_editor_property('animation').get_editor_property('sequence_length') * cad / 2 / base[i]
        s.set_editor_property('rate_scale', base[i] * k); samples[i] = s; out.append((round(y), round(base[i], 3), round(base[i] * k, 3)))
    bs.set_editor_property('sample_data', samples)
    ok = unreal.EditorAssetLibrary.save_loaded_asset(bs, False)
    del bs, samples
    json.dump(dict(walk_s=ws, run_s=rs, run_cadence=cad, saved=ok, rates=out), open(os.path.join(D, 'tfp_stride.json'), 'w'), indent=1)
    print('TFP_STRIDE', ws, rs, ok)
main(); del main
