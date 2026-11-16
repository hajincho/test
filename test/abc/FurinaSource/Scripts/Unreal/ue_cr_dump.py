"""Dumps Control Rig nodes whose name contains argv substrings: pins with default values and links -> Data/cr_dump.json. usage: py ue_cr_dump.py Fing"""
import unreal, json, sys
keys = sys.argv[1:] or ['Fing']
bp = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = bp.get_controller_by_name('RigVMModel') or bp.get_controller(); g = c.get_graph(); R = {}
for n in g.get_nodes():
    nm = n.get_name()
    if any(k in nm for k in keys):
        pins = []
        for p in n.get_pins():
            pins.append([str(p.get_name()), str(p.get_default_value())[:120], [str(l.get_source_pin().get_pin_path()) if l.get_target_pin().get_pin_path() == p.get_pin_path() else str(l.get_target_pin().get_pin_path()) for l in p.get_links()]])
        R[nm] = pins
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\cr_dump.json', 'w'), indent=1); print('CR_DUMP', len(R))
