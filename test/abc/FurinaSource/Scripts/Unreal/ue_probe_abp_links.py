"""Lists the pose links around the rifle nodes in ABP_Furina (read-only)."""
import unreal, json
def main():
    R = {}
    bp = unreal.load_asset('/Game/Furina/ABP_Furina')
    for cls in (unreal.AnimGraphNode_Slot, unreal.AnimGraphNode_LayeredBoneBlend, unreal.AnimGraphNode_ModifyCurve, unreal.AnimGraphNode_ControlRig,
                unreal.AnimGraphNode_TwoWayBlend, unreal.AnimGraphNode_Root):
        for n in unreal.AnimationLibrary.get_nodes_of_class(bp, cls, True):
            d = {}
            for pin_name in ('Source', 'SourcePose', 'BasePose', 'BlendPoses_0', 'A', 'B', 'Result', 'Pose', 'CurveValues_0'):
                p = n.find_input_pin(pin_name) or n.find_output_pin(pin_name)
                if p: d[pin_name] = [q.get_owning_node().get_name() for q in p.list_connected_pins()]
            R[n.get_name()] = d
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\abp_links.json', 'w'), indent=1)
    print('ABP_LINKS_DONE')
main()
del main
