"""Editor: every bone of the Furina rig hierarchy with parent, reference (initial global) position and the bone's direct children count -> Data/bones.json"""
import unreal, json, traceback
def main():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); h = cr.get_hierarchy(); out = {}
    for k in h.get_bones():
        ps = h.get_parents(k); t = h.get_global_transform(k, True).translation
        out[str(k.name)] = dict(parent=str(ps[0].name) if ps else None, pos=[round(t.x, 1), round(t.y, 1), round(t.z, 1)])
    json.dump(out, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bones.json', 'w'), indent=0); print('BONES', len(out))
    del h, cr
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\bones.json', 'w'))
