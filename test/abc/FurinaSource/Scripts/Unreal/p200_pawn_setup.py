"""1단계(폰 BP): 권총 컴포넌트/상태 플래그/변수 추가.  열린 에디터(Remote Execution)에서 실행, 저장은 마지막에.
 - 컴포넌트: FurinaPistolFrame(SM_P200_Frame, 부모 FurinaRifle) / FurinaPistolSlide(SM_P200_Slide, 부모 Frame)
   소총 로컬 좌표: 원점 = Grip, 전방 +Y, 위 +Z.  권총 모델: X 전방, Y 오른쪽, Z 위  => 회전 yaw +90.
   방아쇠(권총 로컬 +5.0 앞, -1.8 아래) 를 소총 Trigger 소켓(0, 0.73, -1.17) 에 맞춘다 -> 위치 (0, -4.27, 0.63)
 - 플래그(SceneComponent): FurinaPistolOn(권총 장착), FurinaSwapping(교체 중)
 - 변수: FurinaSlideTarget, FurinaSlideCur, FurinaSwapTarget, FurinaSwapCur (float), FurinaAmmoStash, FurinaReserveStash, FurinaSwapTmp (int)"""
import unreal, json, traceback
EAL = unreal.EditorAssetLibrary; BEL = unreal.BlueprintEditorLibrary
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
R = {'log': []}
bp = unreal.load_asset(PAWN)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
def handles(): return {str(lib.get_variable_name(lib.get_data(h))): h for h in sub.k2_gather_subobject_data_for_blueprint(bp)}
def comp(name): return lib.get_associated_object(lib.get_data(handles()[name]))
def add(name, cls, parent):
    if name in handles(): return
    h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles()[parent], new_class=cls, blueprint_context=bp))
    sub.rename_subobject(h, unreal.Text(name)); R['log'].append('added ' + name)
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-700:]])
def comps():
    add('FurinaPistolFrame', unreal.StaticMeshComponent, 'FurinaRifle')
    add('FurinaPistolSlide', unreal.StaticMeshComponent, 'FurinaPistolFrame')
    fr = comp('FurinaPistolFrame'); sl = comp('FurinaPistolSlide')
    fr.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/P200/SM_P200_Frame'))
    sl.set_editor_property('static_mesh', unreal.load_asset('/Game/Furina/P200/SM_P200_Slide'))
    fr.set_editor_property('relative_location', unreal.Vector(0.0, -4.27, 0.63)); fr.set_editor_property('relative_rotation', unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
    sl.set_editor_property('relative_location', unreal.Vector(0, 0, 0)); sl.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=0, yaw=0))
    for c in (fr, sl):
        c.set_editor_property('visible', False)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('cast_shadow', True)
    for name in ('FurinaPistolOn', 'FurinaSwapping'):
        add(name, unreal.SceneComponent, 'FurinaMesh')
        c = comp(name); c.set_editor_property('auto_activate', False); c.set_editor_property('component_tags', [name])
    return [str(comp('FurinaPistolFrame').get_editor_property('relative_location')), 'visible', comp('FurinaPistolFrame').get_editor_property('visible')]
def variables():
    ftype = BEL.get_basic_type_by_name('real') if False else None
    out = []
    existing = [str(x) for x in BEL.list_member_variable_names(bp)]
    for name, tname in (('FurinaSlideTarget', 'float'), ('FurinaSlideCur', 'float'), ('FurinaSwapTarget', 'float'), ('FurinaSwapCur', 'float'),
                        ('FurinaAmmoStash', 'int'), ('FurinaReserveStash', 'int'), ('FurinaSwapTmp', 'int')):
        if name in existing: out.append(name + ':exists'); continue
        t = BEL.get_basic_type_by_name(tname)
        out.append([name, BEL.add_member_variable(bp, name, t)])
    return out
step('components', comps); step('variables', variables)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
cdo = unreal.get_default_object(bp.generated_class())
def defaults():
    cdo.set_editor_property('FurinaAmmoStash', 8); cdo.set_editor_property('FurinaReserveStash', 96)
    return [cdo.get_editor_property('FurinaAmmoStash'), cdo.get_editor_property('FurinaReserveStash')]
step('defaults', defaults)
BEL.compile_blueprint(bp); R['status2'] = str(bp.get_editor_property('status'))
print('P200_PAWN_SETUP', json.dumps(R, default=str, ensure_ascii=False)[:2500])
