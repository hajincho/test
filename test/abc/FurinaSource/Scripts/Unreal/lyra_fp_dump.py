"""Lyra 에디터(열린 에디터에서 `py <파일> keep`): 푸리나 폰의 1인칭 카메라/마우스 상하/재장전/총구 관련 구조 덤프 -> Data/lyra_fp_dump.json
 - 카메라 컴포넌트 계층과 설정 (UseControllerRotation, 부착 대상)
 - 이벤트 그래프에서 Pitch/ControlRotation/Look/FirstPerson/Reload/Muzzle/SpawnActor/Bullet 관련 노드와 연결"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_fp_dump.json'
R = {}
try:
    bp = unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    cdo = unreal.get_default_object(bp.generated_class())
    comps = {}
    for c in cdo.get_components_by_class(unreal.SceneComponent):
        row = {'class': c.get_class().get_name()}
        try: row['parent'] = c.get_attach_parent().get_name() if c.get_attach_parent() else None
        except Exception: pass
        try: row['socket'] = str(c.get_attach_socket_name())
        except Exception: pass
        try: row['rel_loc'] = str(c.get_editor_property('relative_location')); row['rel_rot'] = str(c.get_editor_property('relative_rotation'))
        except Exception: pass
        if isinstance(c, unreal.CameraComponent):
            for p in ('use_pawn_control_rotation', 'field_of_view'):
                try: row[p] = str(c.get_editor_property(p))
                except Exception: pass
        if isinstance(c, unreal.SpringArmComponent):
            for p in ('use_pawn_control_rotation', 'target_arm_length', 'inherit_pitch', 'inherit_yaw'):
                try: row[p] = str(c.get_editor_property(p))
                except Exception: pass
        comps[c.get_name()] = row
    R['components'] = comps
    for p in ('use_controller_rotation_pitch', 'use_controller_rotation_yaw', 'use_controller_rotation_roll'):
        try: R[p] = str(cdo.get_editor_property(p))
        except Exception as e: R[p] = 'ERR'
    KEYS = ('pitch', 'controlrotation', 'control rotation', 'baseaim', 'look', 'firstperson', 'reload', 'muzzle', 'spawn', 'bullet', 'invert', 'negat', 'multiply', 'setrelativerotation', 'setworldrotation', 'camera')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph'); out = {}
    for n in ed.list_all_nodes():
        t = str(n.get_node_title()).replace('\n', ' ')
        if any(k in t.lower() for k in KEYS):
            pins = []
            for p in n.list_all_pins():
                con = [c.get_owning_node().get_name() + '.' + str(c.get_pin_name()) for c in p.list_connected_pins()]
                if con or p.get_pin_value(): pins.append([str(p.get_pin_name()), str(p.get_pin_value())[:70], con[:3]])
            out[n.get_name()] = {'title': t, 'pins': pins}
    R['nodes'] = out; R['node_count'] = len(out)
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FP_DUMP', R.get('node_count'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
