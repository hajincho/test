"""Editor: export_text of ABP_Furina's AnimGraphNode_AnimDynamics nodes (node struct) + pin names -> Data/animdyn_dump.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
def main():
    ab = unreal.load_asset('/Game/Furina/ABP_Furina'); R = {}
    for n in unreal.AnimationLibrary.get_nodes_of_class(ab, unreal.AnimGraphNode_AnimDynamics, True):
        R[n.get_name()] = dict(text=n.get_editor_property('node').export_text(), pins=[str(p.get_pin_name()) for p in n.list_all_pins()], title=str(n.get_node_title()).replace('\n', ' '))
    json.dump(R, open(D + r'\animdyn_dump.json', 'w'), indent=1, ensure_ascii=False); print('ANIMDYN', list(R))
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(D + r'\animdyn_dump.json', 'w'))
