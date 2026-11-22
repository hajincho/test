"""읽기 전용: 사격 조준 노드 덤프 -> Saved/AimDump.json"""
import json, re
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
pawn = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph')
pat = re.compile(r'(Sight|AimElev|Aim|Spawn|Muzzle|Zero|BulletXf|Elev|ShotDir|SpawnDir|Spread|Cone|P2_SpawnP220|FPF_Rifle|BulletSpeed)', re.I)
for n in ed.list_all_nodes():
    nm = n.get_name()
    if not pat.search(nm) or nm.startswith(('HFX_', 'PSR_', 'STC_', 'PIP_', 'PistolCase_')): continue
    pins = []
    for p in list(n.list_input_pins()) + list(n.list_output_pins()):
        c = [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]
        v = str(p.get_pin_value())[:60]
        if c or v not in ('', 'None'): pins.append([str(p.get_pin_name()), v, c[:4]])
    R[nm] = pins
bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
if bp:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_associated_object(lib.get_data(h))
        if isinstance(o, unreal.ProjectileMovementComponent): R['bullet_pm'] = {'initial_speed': o.get_editor_property('initial_speed'), 'max_speed': o.get_editor_property('max_speed'), 'gravity': o.get_editor_property('projectile_gravity_scale')}
R['done'] = True; (ROOT / 'Saved' / 'AimDump.json').write_text(json.dumps(R, indent=1), encoding='utf-8')
