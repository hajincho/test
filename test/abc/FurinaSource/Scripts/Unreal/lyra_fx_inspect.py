"""에디터(읽기 전용, 2026-11-21): 총구 효과·반동·흔들림·조준경 작업 전 현황 덤프 -> Saved/FXInspect.json("done": true)
 - 캐릭터 BP 그래프에서 반동(RecGain)·흔들림(Shk)·총구 화염(Flash/FNS/Spark) 관련 노드와 연결
 - FPVM 메시 재질 슬롯 이름, VM_Gun 기준 자세(컴포넌트 공간) 변환
 - NS_MuzzleFlash 사용자 매개변수"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
def pins(n):
    out = []
    for p in list(n.list_input_pins()) + list(n.list_output_pins()) if hasattr(n, 'list_input_pins') else []:
        try: out.append([str(p.get_pin_name()), str(p.get_pin_value())[:80], [q.get_owning_node().get_name() + '.' + str(q.get_pin_name()) for q in p.list_connected_pins()]])
        except Exception as e: out.append([str(e)[:60]])
    return out
try:
    pawn = unreal.load_asset(PAWN); ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(pawn, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    keys = ('RecGain', 'RecG1', 'RecV', 'RecH', 'AdsGain', 'Shk', 'FNS_', 'Flash', 'Spark', 'CaseSpawn', 'Recoil', 'TpGain', 'Mult2', 'StMul', 'HideViewmodel', 'SetActive')
    R['nodes'] = {k: pins(n) for k, n in nodes.items() if any(s in k for s in keys)}
    R['n_nodes'] = len(nodes)
except Exception: R['bp_error'] = traceback.format_exc()[-1200:]
try:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); out = {}
    for folder, name in (('Kar98k', 'Kar98k_Interior'), ('Kar98k', 'Kar98k_ZF39'), ('Kar98k', 'Kar98k_ZF41'), ('G43', 'G43_Interior'), ('G43', 'G43_ZF4'),
                         ('P38', 'P38'), ('P08', 'P08'), ('PP', 'PP'), ('MP40', 'MP40'), ('MP38', 'MP38'), ('STG44', 'STG44')):
        mesh = unreal.load_asset(f'/Game/Furina/FPVM/{folder}/SK_FPVM_{name}')
        if not mesh: out[name] = 'missing'; continue
        a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); c = a.get_component_by_class(unreal.SkeletalMeshComponent)
        t = c.get_socket_transform('VM_Gun', unreal.RelativeTransformSpace.RTS_COMPONENT)
        q = t.rotation
        out[name] = {'slots': [str(s.material_slot_name) for s in mesh.materials], 'gun_loc': [t.translation.x, t.translation.y, t.translation.z], 'gun_quat': [q.x, q.y, q.z, q.w],
                     'n_sockets': mesh.num_sockets() if hasattr(mesh, 'num_sockets') else None,
                     'bones': [str(c.get_bone_name(i)) for i in range(c.get_num_bones())][-8:]}
        eas.destroy_actor(a)
    R['meshes'] = out
except Exception: R['mesh_error'] = traceback.format_exc()[-1200:]
try:
    ns = unreal.load_asset('/Game/NiagaraExamples/FX_Weapons/MuzzleFlashes/NS_MuzzleFlash')
    R['ns'] = str(ns)
    try:
        st = ns.get_editor_property('exposed_parameters'); R['ns_params'] = str(st)[:1500]
    except Exception as e: R['ns_params_err'] = str(e)[:200]
except Exception: R['ns_error'] = traceback.format_exc()[-600:]
try:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for path in ('/Game/Furina/M4/BP_M4Flash',):
        bp = unreal.load_asset(path); comps = {}
        for h in sub.k2_gather_subobject_data_for_blueprint(bp):
            d = lib.get_data(h); o = lib.get_associated_object(d); nm = str(lib.get_variable_name(d))
            info = {'class': o.get_class().get_name() if o else None}
            if isinstance(o, unreal.StaticMeshComponent):
                info['mesh'] = o.static_mesh.get_name() if o.static_mesh else None; info['mat'] = [m.get_name() if m else None for m in o.get_materials()]
                info['loc'] = str(o.get_editor_property('relative_location')); info['scale'] = str(o.get_editor_property('relative_scale3d'))
            comps[nm] = info
        R['flash_bp'] = comps
except Exception: R['flash_error'] = traceback.format_exc()[-800:]
R['done'] = True
(ROOT / 'Saved' / 'FXInspect.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('FX_INSPECT done')
