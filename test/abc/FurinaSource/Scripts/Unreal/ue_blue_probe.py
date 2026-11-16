"""Lists light / Niagara / mesh components (with colors and materials) of BP_FurinaBullet, BP_M4Flash, BP_M4MagDrop and the character BP, to find the blue effect seen when firing -> Data/blue_probe.json"""
import unreal, json
S = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
R = {}
for p in ('/Game/Furina/FP/BP_FurinaBullet', '/Game/Furina/M4/BP_M4Flash', '/Game/Furina/M4/BP_M4MagDrop', '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'):
    try: bp = unreal.load_asset(p)
    except Exception as e: R[p] = 'ERR ' + str(e); continue
    d = {}
    for h in S.k2_gather_subobject_data_for_blueprint(bp):
        o = L.get_associated_object(L.get_data(h)); n = str(L.get_variable_name(L.get_data(h))); c = o.get_class().get_name() if o else None
        if c is None: continue
        e = {'class': c}
        if isinstance(o, unreal.LightComponent): e.update(color=str(o.get_editor_property('light_color')), intensity=o.get_editor_property('intensity'), visible=o.get_editor_property('visible'))
        elif isinstance(o, unreal.NiagaraComponent): e.update(asset=str(o.get_editor_property('asset')), auto=o.get_editor_property('auto_activate'))
        elif isinstance(o, unreal.StaticMeshComponent): e.update(mesh=str(o.static_mesh.get_name()) if o.static_mesh else None, mat=[str(m.get_path_name()) for m in o.get_materials()], hidden=o.get_editor_property('hidden_in_game'))
        elif isinstance(o, unreal.ParticleSystemComponent if hasattr(unreal, 'ParticleSystemComponent') else ()): e.update(kind='cascade')
        else: continue
        d[n] = e
    R[p] = d
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\blue_probe.json', 'w'), indent=1); print('BLUE_PROBE')
