"""Read-only inspection for blink, knee IK, and locomotion audio."""
import unreal, json, traceback, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Data', 'character_fixes_diagnosis.json')
R = {}

def prop(obj, name):
    try:
        v = obj.get_editor_property(name)
        if hasattr(v, 'export_text'): return v.export_text()
        return str(v)
    except Exception as e: return 'ERROR: ' + str(e)

try:
    R['engine'] = unreal.SystemLibrary.get_engine_version()
    bp = unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    c = bp.get_controller()
    R['rig_curves'] = [str(k.name) for k in bp.get_hierarchy().get_all_keys(True) if k.type == unreal.RigElementType.CURVE]
    R['rig_nodes'] = {}
    for node in c.get_graph().get_nodes():
        n = node.get_name()
        if any(x in n for x in ('Blink', 'Pole', 'KDir', 'IKW', 'IK', 'Narrow', 'Run', 'Idle')):
            R['rig_nodes'][n] = {str(p.get_name()): {'default': p.get_default_value(), 'links': [l.get_pin_path() for l in p.get_linked_source_pins()]} for p in node.get_pins()}
    ap = unreal.load_asset('/Game/Furina/ABP_Furina')
    R['abp'] = {p: prop(ap,p) for p in ('status', 'target_skeleton', 'ubergraph_pages', 'function_graphs')}
    R['abp_methods'] = [x for x in dir(ap) if any(k in x for k in ('graph', 'node', 'curve', 'compile'))]
    A = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Characters/Mannequins/Animations/'
    R['animations'] = {}
    for path in [A+n for n in ('Walk_InPlace_Anim', 'Walk_Fwd_Anim', 'Run_Fwd_Anim', 'Idle_Anim')] + ['/Game/Furina/Anim/AS_Furina_Idle', '/Game/Furina/Anim/AS_Furina_Walk']:
        a = unreal.load_asset(path)
        if not a: continue
        d = {'length': a.get_play_length(), 'curves': [str(x) for x in unreal.AnimationLibrary.get_animation_curve_names(a, unreal.RawCurveTrackTypes.RCT_FLOAT)]}
        d['notifies'] = []
        for ev in unreal.AnimationLibrary.get_animation_notify_events(a):
            nd = {'text': ev.export_text()}
            for k in ('notify', 'notify_state_class'):
                no = ev.get_editor_property(k)
                if no:
                    nd[k] = {'class': no.get_class().get_path_name(), 'path': no.get_path_name(), 'fields': {q:prop(no,q) for q in ('sound', 'volume_multiplier', 'pitch_multiplier', 'follow', 'attach_name')}}
            d['notifies'].append(nd)
        R['animations'][path] = d
    char = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    cdo = unreal.get_default_object(char.generated_class())
    R['character'] = {p:prop(cdo,p) for p in ('mesh', 'character_movement')}
    R['components'] = [{'name':x.get_name(),'class':x.get_class().get_path_name(), 'fields':{p:prop(x,p) for p in ('sound', 'auto_activate', 'skeletal_mesh_asset', 'anim_class', 'visibility_based_anim_tick_option')}} for x in cdo.get_components_by_class(unreal.ActorComponent)]
    R['api'] = {name: [x for x in dir(getattr(unreal,name)) if any(k in x for k in ('notify', 'curve', 'graph', 'node', 'reload', 'compile'))] for name in ('AnimationLibrary','BlueprintEditorLibrary','EditorLoadingAndSavingUtils', 'RigVMController', 'AnimGraphNode_ControlRig')}
except Exception:
    R['error'] = traceback.format_exc()
with open(OUT,'w',encoding='utf-8') as f: json.dump(R,f,ensure_ascii=False,indent=2,default=str)
print('CHARACTER_FIXES_DIAGNOSIS_DONE', OUT)
