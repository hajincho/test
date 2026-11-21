"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 이 스크립트만 한 번): 3인칭 등 매기/권총 홀스터용 컴포넌트를 ThirdPersonCharacter_BP 에 추가한다.
 - FurinaSlingM4   : SkeletalMeshComponent (SK_M4A1), 부모 FurinaMesh, 소켓 Spine (등에 맨 소총)
 - FurinaHolsterFrame / FurinaHolsterSlide : StaticMesh (SM_P220_Frame / Slide), 부모 FurinaMesh(소켓 Hips) / Frame  (허리춤 홀스터 권총)
 처음엔 보이지 않음(visible False), 충돌 없음. 상대 위치/회전은 임시값 -> lyra_gear_place.py 가 PIE 뼈 변환으로 계산해 덮어쓴다.   -> Data/lyra_gear_comps.json"""
import unreal, json, traceback
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_gear_comps.json'
R = {'log': []}
def run():
    bp = unreal.load_asset(PAWN)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
    def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
    def add(name, cls, parent):
        if name in handles(): R['log'].append(name + ' exists'); return
        h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()[parent], new_class=cls, blueprint_context=bp)); sub.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
    add('FurinaSlingM4', unreal.SkeletalMeshComponent, 'FurinaMesh'); add('FurinaHolsterFrame', unreal.StaticMeshComponent, 'FurinaMesh'); add('FurinaHolsterSlide', unreal.StaticMeshComponent, 'FurinaHolsterFrame')
    rf = comp('FurinaRifle')
    s = comp('FurinaSlingM4'); s.set_editor_property('skeletal_mesh_asset', rf.get_editor_property('skeletal_mesh_asset')); R['rifle_mesh'] = str(rf.get_editor_property('skeletal_mesh_asset'))
    fr = comp('FurinaHolsterFrame'); sl = comp('FurinaHolsterSlide')
    fr.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/P220/SM_P220_Frame')); sl.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/P220/SM_P220_Slide'))
    for c in (s, fr, sl):
        c.set_editor_property('visible', False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property('cast_shadow', True)
    for c, sock in ((s, 'Spine'), (fr, 'Hips')):
        try: c.set_editor_property('attach_socket_name', sock); R['log'].append('socket ' + sock + ' -> ' + str(c.get_editor_property('attach_socket_name')))
        except Exception as e: R['log'].append('socket err ' + str(e)[:80])
    sl.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); sl.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=0, yaw=0))
    # 렌더 설정은 소총 컴포넌트에서 복사
    for pn in ('cast_shadow', 'render_in_main_pass', 'render_in_depth_pass', 'cast_contact_shadow', 'lighting_channels', 'receives_decals'):
        try: s.set_editor_property(pn, rf.get_editor_property(pn))
        except Exception: pass
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False) if bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del bp, sub, lib
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_GEAR_COMPS', R.get('status'), R.get('error', ''))
import gc; gc.collect()
