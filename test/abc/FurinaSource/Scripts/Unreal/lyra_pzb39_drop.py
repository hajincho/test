"""Stage a world-space drop and pickup during the standing-only recovery."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, chain, literal, relay, wire
from lyra_pzb39 import API, ASSETS, FOLDER, ROOT, save
from lyra_pzb39_reaction import SCENE, value
from lyra_pzb39_recovery_pose import DROP_POINT, OUT, PICKUP_TIME


PROP = 'FurinaPzbDropped'
FIELDS = {
    'FurinaPzbReleaseWorld': 'vector',
    'FurinaPzbFloorWorld': 'vector',
    'FurinaPzbDropHeading': 'real',
}


def import_drop_mesh(world):
    key = 'SM_PZB39_Dropped'
    relative = f'{FOLDER}/{key}'
    if ASSETS.does_asset_exist(relative):
        return unreal.load_asset(relative)
    ui = unreal.FbxImportUI()
    ui.set_editor_property('automated_import_should_detect_type', False)
    ui.set_editor_property('import_as_skeletal', False)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.static_mesh_import_data.set_editor_property('combine_meshes', True)
    task = unreal.AssetImportTask()
    task.filename = str(ROOT / 'FurinaSource/FBX/FPVM' / (key + '.fbx'))
    task.destination_path = FOLDER
    task.destination_name = key
    task.automated = True
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    prior = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if prior else ' 0'))
    mesh = unreal.load_asset(relative)
    assert mesh
    original = unreal.load_asset('/Game/Furina/Weapons/Germany/pzb39/SM_DE_pzb39')
    old = {str(slot.material_slot_name): slot.material_interface for slot in original.static_materials}
    for index, slot in enumerate(mesh.static_materials):
        material = old.get(str(slot.material_slot_name))
        if material is not None:
            mesh.set_material(index, material)
    assert ASSETS.save_loaded_asset(mesh, False)
    return mesh


def prepare(pawn, model):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = {str(lib.get_variable_name(lib.get_data(handle))): handle
               for handle in sub.k2_gather_subobject_data_for_blueprint(pawn)}
    if PROP not in handles:
        anchor = next(handle for name, handle in handles.items() if name == 'FurinaMesh')
        handle, issue = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=anchor, new_class=unreal.StaticMeshComponent, blueprint_context=pawn))
        assert not str(issue), str(issue)
        assert sub.rename_subobject(handle, unreal.Text(PROP))
    else:
        handle = handles[PROP]
    prop = lib.get_associated_object(lib.get_data(handle))
    prop.set_static_mesh(model)
    prop.set_editor_property('visible', False)
    prop.set_editor_property('absolute_location', True)
    prop.set_editor_property('absolute_rotation', True)
    prop.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    names = {str(name) for name in API.list_member_variable_names(pawn)}
    for name, kind in FIELDS.items():
        if kind == 'vector':
            pin_type = unreal.EdGraphPinType()
            assert pin_type.import_text('(PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.Vector")')
        else:
            pin_type = API.get_basic_type_by_name(kind)
        if name not in names:
            assert API.add_member_variable(pawn, name, pin_type), name
    API.compile_blueprint(pawn)


def curve_edits(graph):
    for tag, start, end in (('Back', .045, .57), ('Level', 1.23, 1.86),
                            ('FindHand', 1.42, 2.02), ('Horizon', 2.63, 3.57)):
        literal(graph.nodes['PzbBalance_' + tag + 'AfterStart'], 'B', start)
        literal(graph.nodes['PzbBalance_' + tag + 'Normalize'], 'B', 1. / (end - start))
    literal(graph.nodes['PzbBalance_SwingBack'], 'B', 78.)
    literal(graph.nodes['PzbBalance_RecoverSeconds'], 'A', unreal.load_asset(OUT).get_play_length())


def frame_pickup(pawn):
    graph = Graph(pawn, 'PzbPickupView_')
    if 'PzbPickupView_ApplyEyes' in graph.nodes:
        finish_gaze(graph)
        return
    camera = graph.get('FPCamera')
    controller_rotation = graph.nodes['PzbBalance_TrackView'].find_result_pin()
    target = graph.nodes['PzbLand_SeeSupport'].find_result_pin()
    influence = graph.nodes['PzbLand_FocusTime'].find_result_pin()

    def use_controller(name, enabled):
        return graph.call(name, ENGINE + 'KismetSystemLibrary:SetBoolPropertyByName',
                          Object=camera, PropertyName='bUsePawnControlRotation', Value=enabled)

    for before, action in (
        ('PzbDrop_ShowWorldProp', use_controller('TakeHeadControl', False)),
        ('PzbDrop_ReturnToViewmodel', use_controller('ReturnHeadControl', True)),
    ):
        relay(graph.nodes[before].find_then_pin(), action.find_execute_pin(), action.find_then_pin())

    delta = value(graph, 'TowardProp', MATH + 'NormalizedDeltaRotator', A=target, B=controller_rotation)
    delta_axes = graph.call('HeadTurnAxes', MATH + 'BreakRotator', InRot=delta)
    axes = graph.call('PlayerAxes', MATH + 'BreakRotator', InRot=controller_rotation)
    yaw = value(graph, 'YawLimit', MATH + 'FClamp', Value=delta_axes.find_output_pin('Yaw'), Min=-83., Max=83.)
    turn = value(graph, 'HeadTurn', MATH + 'Multiply_DoubleDouble', A=yaw, B=influence)
    result = value(graph, 'ViewYaw', MATH + 'Add_DoubleDouble', A=axes.find_output_pin('Yaw'), B=turn)
    desired = value(graph, 'Gaze', MATH + 'MakeRotator', Pitch=axes.find_output_pin('Pitch'), Yaw=result,
                    Roll=axes.find_output_pin('Roll'))
    point = graph.call('ApplyEyes', SCENE + 'K2_SetWorldRotation', camera,
                       NewRotation=desired, bSweep=False, bTeleport=True)
    chain(graph.nodes['PzbDrop_PlaceDuringFall'].find_then_pin(), [point])
    finish_gaze(Graph(pawn, 'PzbPickupView_'))


def finish_gaze(graph):
    if 'PzbPickupView_GroundPitchMix' in graph.nodes:
        return
    pitch = graph.nodes['PzbPickupView_PlayerAxes'].find_output_pin('Pitch')
    target = graph.nodes['PzbLand_HandPitch'].find_output_pin('Pitch')
    weight = graph.nodes['PzbLand_FocusTime'].find_result_pin()
    safe = value(graph, 'LimitGroundPitch', MATH + 'FClamp', Value=target, Min=-87., Max=-12.)
    followed = value(graph, 'GroundPitchMix', MATH + 'Lerp', A=pitch, B=safe, Alpha=weight)
    up = graph.nodes['PzbPickupView_Gaze'].find_input_pin('Pitch')
    up.break_pin_links()
    wire(followed, up)
    limit = graph.nodes['PzbPickupView_YawLimit']
    literal(limit, 'Min', -97.)
    literal(limit, 'Max', 97.)


def install(pawn):
    graph = Graph(pawn, 'PzbDrop_')
    if 'PzbDrop_PlaceDuringFall' in graph.nodes:
        curve_edits(graph)
        return
    owner = graph.nodes['K2Node_FPF_Self'].find_output_pin('self')
    prop = graph.get(PROP)
    body = graph.get('FurinaMesh')
    tick = graph.nodes['PzbBalance_Elapsed'].find_result_pin()

    def math_(tag, function, **pins):
        return value(graph, tag, MATH + function, **pins)

    def m(tag, a, b):
        return math_(tag, 'Multiply_DoubleDouble', A=a, B=b)

    def sv(tag, vec, factor):
        return math_(tag, 'Multiply_VectorFloat', A=vec, B=factor)

    def av(tag, a, b):
        return math_(tag, 'Add_VectorVector', A=a, B=b)

    def smooth(tag, start, finish):
        time = math_(tag + 'Time', 'Subtract_DoubleDouble', A=tick, B=start)
        clamp = math_(tag + 'Clamp', 'FClamp', Value=m(tag + 'Rate', time, 1./(finish-start)), Min=0., Max=1.)
        return math_(tag, 'FInterpEaseInOut', A=0., B=1., Alpha=clamp, Exponent=2.)

    def button(tag, show):
        return graph.call(tag, SCENE + 'SetVisibility', prop, bNewVisibility=show, bPropagateToChildren=False)

    def position(tag, loc, rotation):
        return graph.call(tag, SCENE + 'K2_SetWorldLocationAndRotation', prop, NewLocation=loc, NewRotation=rotation,
                          bSweep=False, bTeleport=True)

    def rotation(tag, pitch, yaw, roll):
        return math_(tag, 'MakeRotator', Pitch=pitch, Yaw=yaw, Roll=roll)

    yaw_now = value(graph, 'ActorRotation', ENGINE + 'Actor:K2_GetActorRotation', owner)
    axes = graph.call('Heading', MATH + 'BreakRotator', InRot=yaw_now)
    yaw = axes.find_output_pin('Yaw')
    forward = value(graph, 'Forward', ENGINE + 'Actor:GetActorForwardVector', owner)
    right = value(graph, 'Right', ENGINE + 'Actor:GetActorRightVector', owner)
    root = value(graph, 'BodyRoot', SCENE + 'K2_GetComponentLocation', body)
    first = value(graph, 'ReleaseGrip', SCENE + 'GetSocketLocation', graph.get('FurinaFPVM'), InSocketName='Right-wrist')
    wrist = value(graph, 'RecoveryHand', SCENE + 'GetSocketLocation', body, InSocketName='Right-wrist')
    floor_xy = av('FeetOffset', sv('GroundForward', forward, DROP_POINT[0]), sv('GroundRight', right, DROP_POINT[1]))
    floor_anchor = av('GripAtRest', av('GroundNearBody', root, floor_xy), '0,0,10.5')
    heading = graph.get('FurinaPzbDropHeading')
    start = graph.get('FurinaPzbReleaseWorld')
    floor = graph.get('FurinaPzbFloorWorld')
    play = graph.nodes['PzbBalance_HideCarriedViewmodel'].find_then_pin()
    former = list(play.list_connected_pins())
    play.break_pin_links()
    drop = chain(play, [
        graph.store('ReleaseAt', 'FurinaPzbReleaseWorld', first),
        graph.store('MarkLanding', 'FurinaPzbFloorWorld', floor_anchor),
        graph.store('KeepHeading', 'FurinaPzbDropHeading', yaw),
        position('ShowAtHand', start, rotation('HoldBeforeDrop', 2., heading, -9.)),
        button('ShowWorldProp', True),
    ])
    for pin in former:
        wire(drop, pin)

    dropping = smooth('FallFlight', .04, .67)
    fall = math_('Flight', 'VLerp', A=start, B=floor, Alpha=dropping)
    shock = math_('BounceTime', 'FClamp',
                  Value=math_('AfterImpact', 'Subtract_DoubleDouble', A=tick, B=.66), Min=0., Max=.26)
    rise = math_('SkipAtContact', 'Sin', A=m('BounceArc', shock, 12.083))
    weighted = m('BounceEnvelope', rise, 4.5)
    gap = math_('LiftFromGround', 'MakeVector', X=0., Y=0., Z=weighted)
    drop_loc = av('SettledProp', fall, gap)
    pickup = smooth('PickupBlend', PICKUP_TIME, PICKUP_TIME + .12)
    world = math_('FollowHandAfterContact', 'VLerp', A=drop_loc, B=wrist, Alpha=pickup)
    pitch = math_('Tip', 'Lerp', A=-2., B=14., Alpha=dropping)
    lean = math_('Roll', 'Lerp', A=-9., B=77., Alpha=dropping)
    roll = math_('CarryRoll', 'Lerp', A=lean, B=11., Alpha=pickup)
    tip = math_('CarryPitch', 'Lerp', A=pitch, B=9., Alpha=pickup)
    yaw_plus = math_('Sideways', 'Add_DoubleDouble', A=heading, B=m('TurnInFlight', dropping, 26.))
    final_yaw = math_('CarryYaw', 'Lerp', A=yaw_plus, B=heading, Alpha=pickup)
    move = position('PlaceDuringFall', world, rotation('FallingAndLifted', tip, final_yaw, roll))
    eye_path = graph.nodes['PzbBalance_TrackRememberRoll'].find_then_pin()
    upright = graph.branch('OnlyStandingDrop', graph.get('FurinaPzbStand'))
    wire(eye_path, upright.find_execute_pin())
    wire(upright.find_then_pin(), move.find_execute_pin())
    clean = button('ReturnToViewmodel', False)
    original = graph.nodes['PzbBalance_RestoreLocomotion'].find_then_pin()
    relay(original, clean.find_execute_pin(), clean.find_then_pin())

    # Look up while supine, then use the actual prop's world position as the gaze target.
    look = graph.nodes['PzbLand_SeeSupport'].find_input_pin('Target')
    look.break_pin_links()
    current_prop = value(graph, 'TrackDroppedMesh', SCENE + 'K2_GetComponentLocation', prop)
    wire(current_prop, look)
    literal(graph.nodes['PzbLand_FloorPitch'], 'Max', -12.)
    curve_edits(graph)


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN)
    graph = Graph(pawn)
    if 'PzbDrop_ReleaseAt' in graph.nodes and 'PzbDrop_PlaceDuringFall' not in graph.nodes:
        graph.editor.remove_nodes([node for name, node in graph.nodes.items() if name.startswith('PzbDrop_')])
        after_hide = graph.nodes['PzbBalance_HideCarriedViewmodel'].find_then_pin()
        if not after_hide.list_connected_pins():
            wire(after_hide, graph.nodes['PzbBalance_FallAndStand'].find_execute_pin())
    prepare(pawn, import_drop_mesh(editor.get_editor_world()))
    install(pawn)
    frame_pickup(pawn)
    save(pawn)
    print('PZB39_DROP_AND_PICKUP_SAVED')


if __name__ == '__main__':
    main()
