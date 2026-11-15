"""PIE: coat / skirt chains (HB* bones: 14 roots under Hips + descendants). For every root bone: mesh-space position of the root and of its deepest descendant (chain tip) and the chain direction
(unit vector root -> tip), plus the Hips position -> Data/cape_probe_<tag>.json. Stand / lie as you like first. usage: py ue_cape_probe.py <tag>"""
import unreal, json, sys, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
TAG = sys.argv[1] if len(sys.argv) > 1 else 'x'
def main():
    bones = json.load(open(D + r'\bones.json'))
    kids = {}
    for n, v in bones.items(): kids.setdefault(v['parent'], []).append(n)
    roots = [n for n in kids.get('Hips', []) if n.startswith('HB')]
    def deepest(n):
        best = (0, n)
        for c in kids.get(n, []):
            d, t = deepest(c); best = max(best, (d + 1, t))
        return best
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); pc = unreal.GameplayStatics.get_player_character(w, 0)
    m = [c for c in pc.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'FurinaMesh'][0]; T = m.get_world_transform()
    def M(b): return unreal.MathLibrary.inverse_transform_location(T, m.get_socket_location(b))
    R = {'hips': [round(x, 1) for x in M('Hips').to_tuple()], 'roots': {}}
    for r in roots:
        depth, tip = deepest(r); a = M(r); b = M(tip); d = b - a; L = d.length()
        R['roots'][r] = dict(tip=tip, depth=depth, root=[round(x, 1) for x in a.to_tuple()], tip_pos=[round(x, 1) for x in b.to_tuple()], dir=[round(x / max(L, 1e-6), 3) for x in d.to_tuple()], length=round(L, 1))
    json.dump(R, open(D + r'\cape_probe_%s.json' % TAG, 'w'), indent=1); print('CAPE_PROBE', TAG, len(roots))
    del w, pc, m
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\cape_probe_%s.json' % TAG, 'w'), indent=1)
