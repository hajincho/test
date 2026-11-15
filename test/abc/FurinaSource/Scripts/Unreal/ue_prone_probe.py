"""Editor: capsule / movement defaults of ThirdPersonCharacter_BP and the first bones of the Furina rig hierarchy (name -> parent) -> Data/prone_probe.json"""
import unreal, json
def main():
    R = {}
    ch = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    cdo = unreal.get_default_object(ch.generated_class())
    cap = cdo.get_editor_property('capsule_component'); cmc = cdo.get_editor_property('character_movement')
    R['capsule'] = dict(radius=cap.get_editor_property('capsule_radius'), half=cap.get_editor_property('capsule_half_height'))
    R['cmc'] = {k: cmc.get_editor_property(k) for k in ('crouched_half_height', 'max_walk_speed', 'max_walk_speed_crouched', 'jump_z_velocity', 'can_walk_off_ledges_when_crouching', 'braking_deceleration_walking')}
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); h = cr.get_hierarchy()
    bones = {}
    for k in h.get_bones():
        ps = h.get_parents(k); bones[str(k.name)] = str(ps[0].name) if ps else None
    R['n_bones'] = len(bones)
    R['bones'] = {n: p for n, p in bones.items() if any(s in n.lower() for s in ('hip', 'root', 'spine', 'chest', 'neck', 'head', 'leg', 'knee', 'ankle', 'toe', 'arm', 'elbow', 'wrist', 'shoulder'))}
    R['root_children'] = [n for n, p in bones.items() if p in (None, '', 'None')]
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\prone_probe.json', 'w'), indent=1); print('PRONE_PROBE', R['capsule'], R['cmc'], R['root_children'])
    del h, cr, cdo, cap, cmc, ch
import traceback
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\prone_probe.json', 'w'), indent=1)
