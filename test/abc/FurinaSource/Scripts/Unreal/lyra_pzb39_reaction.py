"""Connect the full-body recovery and head/eye response to a confirmed in-game shot."""
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import ENGINE, MATH, PAWN, Graph, chain, wire
from lyra_pzb39 import API, matches, save
from lyra_pzb39_recovery_pose import OUT


SYSTEM = ENGINE + 'KismetSystemLibrary:'
GAME = ENGINE + 'GameplayStatics:'
SCENE = ENGINE + 'SceneComponent:'
TICK = 'FurinaPzb39BalanceUpdate'


def value(graph, name, method, target=None, **pins):
    return graph.call(name, method, target, **pins).find_result_pin()


def improve_floor_view(graph):
    if 'PzbLand_HandPitch' in graph.nodes:
        return
    graph.prefix = 'PzbLand_'
    active = value(graph, 'Plant', MATH + 'BooleanAND', A=graph.get('FurinaPzbBusy'), B=graph.get('FurinaPzbStand'))
    normal = value(graph, 'NormalArms', MATH + 'Not_PreBool', A=active)
    for key in ('FPA_BrR', 'FPA_BrL'):
        arm_change = graph.nodes.get(key)
        if not arm_change:
            continue
        source = arm_change.find_input_pin('Condition')
        upstream, = source.list_connected_pins()
        source.break_pin_links()
        wire(value(graph, 'Allow' + key, MATH + 'BooleanAND', A=normal, B=upstream), source)

    fall = graph.nodes['PzbBalance_FallAndStand']
    outputs = list(fall.find_then_pin().list_connected_pins())
    fall.find_then_pin().break_pin_links()
    mesh = graph.get('FurinaMesh')
    end = chain(fall.find_then_pin(), [
        graph.call('ShowLeftSupport', ENGINE + 'SkinnedMeshComponent:UnHideBoneByName', mesh, BoneName='Left-arm'),
        graph.call('ShowRightHand', ENGINE + 'SkinnedMeshComponent:UnHideBoneByName', mesh, BoneName='Right-arm'),
    ])
    for output in outputs:
        wire(end, output)

    target = value(graph, 'Palm', SCENE + 'GetSocketLocation', mesh, InSocketName='MiddleFinger1_L')
    camera = value(graph, 'Eyes', SCENE + 'K2_GetComponentLocation', graph.get('FPCamera'))
    look = value(graph, 'SeeSupport', MATH + 'FindLookAtRotation', Start=camera, Target=target)
    axes = graph.call('HandPitch', MATH + 'BreakRotator', InRot=look)
    pitch = value(graph, 'FloorPitch', MATH + 'FClamp', Value=axes.find_output_pin('Pitch'), Min=-75., Max=-27.)
    ease = graph.nodes['PzbBalance_FindHandEase'].find_result_pin()
    release = graph.nodes['PzbBalance_HorizonEase'].find_result_pin()
    strength = value(graph, 'FocusTime', MATH + 'Subtract_DoubleDouble', A=ease, B=release)
    pitch_node = graph.nodes['PzbBalance_Pitch']
    existing = pitch_node.find_input_pin('A')
    authored, = existing.list_connected_pins()
    existing.break_pin_links()
    focus = value(graph, 'TrackPalm', MATH + 'Lerp', A=authored, B=pitch, Alpha=strength)
    wire(focus, existing)
    # Ease in after the backward impact, then recover the horizon as the feet take the load.
    from lyra_fpvm_optics import literal
    for tag, start, end_seconds in (('FindHand', .68, 1.12), ('Horizon', 1.49, 2.38)):
        literal(graph.nodes['PzbBalance_' + tag + 'AfterStart'], 'B', start)
        literal(graph.nodes['PzbBalance_' + tag + 'Normalize'], 'B', 1. / (end_seconds - start))


def install(pawn):
    graph = Graph(pawn, 'PzbBalance_')
    if 'PzbBalance_ConfirmedShot' in graph.nodes:
        return
    fields = {
        'FurinaPzbBusy': 'bool',
        'FurinaPzbStand': 'bool',
        'FurinaPzbStart': 'real',
        'FurinaPzbOldPitch': 'real',
        'FurinaPzbOldRoll': 'real',
    }
    current = {str(name) for name in API.list_member_variable_names(pawn)}
    for field, kind in fields.items():
        if field not in current:
            assert API.add_member_variable(pawn, field, API.get_basic_type_by_name(kind))
    API.compile_blueprint(pawn)
    graph = Graph(pawn, 'PzbBalance_')
    owner = graph.nodes['K2Node_FPF_Self'].find_output_pin('self')
    controller = value(graph, 'Player', ENGINE + 'Pawn:GetController', owner)
    body = graph.get('FurinaMesh')
    vm = graph.get('FurinaFPVM')
    recovery = unreal.load_asset(OUT)
    assert recovery

    def math_(name, method, **pins):
        return value(graph, name, MATH + method, **pins)

    def add(name, a, b):
        return math_(name, 'Add_DoubleDouble', A=a, B=b)

    def sub(name, a, b):
        return math_(name, 'Subtract_DoubleDouble', A=a, B=b)

    def mul(name, a, b):
        return math_(name, 'Multiply_DoubleDouble', A=a, B=b)

    def compare(name, a, b):
        return math_(name, 'GreaterEqual_DoubleDouble', A=a, B=b)

    def choose(name, condition, a, b):
        return math_(name, 'SelectFloat', bPickA=condition, A=a, B=b)

    def ignore(name, ignore_move):
        return graph.call(name, ENGINE + 'Controller:SetIgnoreMoveInput', controller, bNewMoveInput=ignore_move)

    def visibility(name, show):
        return graph.call(name, SCENE + 'SetVisibility', vm, bNewVisibility=show, bPropagateToChildren=False)

    def track_time():
        return value(graph, 'Clock', GAME + 'GetTimeSeconds')

    def set_timer(name, function, duration):
        return graph.call(name, SYSTEM + 'K2_SetTimer', Object=owner, FunctionName=function,
                          Time=duration, bLooping=True)

    def went_through(source, branch):
        previous = list(source.list_connected_pins())
        source.break_pin_links()
        wire(source, branch.find_execute_pin())
        for pin in previous:
            wire(branch.find_else_pin(), pin)

    shot = matches(graph, 'ConfirmedShot', 'FurinaGameWeaponId')
    went_through(graph.nodes['M4_SetFurinaAmmo'].find_then_pin(), shot)
    movement = value(graph, 'Movement', ENGINE + 'Pawn:GetMovementComponent', owner)
    crouched = value(graph, 'Crouched', ENGINE + 'NavMovementComponent:IsCrouching', movement)
    grounded = value(graph, 'Grounded', ENGINE + 'NavMovementComponent:IsMovingOnGround', movement)
    stand = math_('StandingOnFloor', 'BooleanAND', A=grounded, B=math_('Upright', 'Not_PreBool', A=crouched))
    stance = graph.branch('ChoosePose', stand)
    wire(chain(shot.find_then_pin(), [
        graph.store('StartAt', 'FurinaPzbStart', track_time()),
        graph.store('StartPose', 'FurinaPzbStand', stand),
        graph.store('Activate', 'FurinaPzbBusy', True),
        graph.store('ResetPitch', 'FurinaPzbOldPitch', 0.),
        graph.store('ResetRoll', 'FurinaPzbOldRoll', 0.),
        set_timer('StartEyes', TICK, .016),
    ]), stance.find_execute_pin())
    stop = graph.call('StopMoving', ENGINE + 'MovementComponent:StopMovementImmediately', movement)
    animate = graph.call('FallAndStand', ENGINE + 'SkeletalMeshComponent:PlayAnimation', body,
                         NewAnimToPlay=recovery, bLooping=False)
    chain(stance.find_then_pin(), [ignore('LockMove', True), stop, visibility('HideCarriedViewmodel', False), animate])

    # Check the lock before the viewmodel stores the key, so a pending selection is retried.
    condition = graph.locate('VW_Br_4_').find_input_pin('Condition')
    previous, = condition.list_connected_pins()
    condition.break_pin_links()
    ready = math_('ChoiceReady', 'Not_PreBool', A=graph.get('FurinaPzbBusy'))
    wire(math_('CanSwitch', 'BooleanAND', A=previous, B=ready), condition)
    reload = graph.nodes['HistoryReload_HasWeapon'].find_execute_pin()
    reload_inputs = list(reload.list_connected_pins())
    reload.break_pin_links()
    gate = graph.branch('BlockReloadDuringRecovery', graph.get('FurinaPzbBusy'))
    for pin in reload_inputs:
        wire(pin, gate.find_execute_pin())
    wire(gate.find_else_pin(), reload)

    step = graph.editor.add_custom_event_node(TICK)
    step.rename('PzbBalance_Update')
    elapsed = sub('Elapsed', value(graph, 'TickClock', GAME + 'GetTimeSeconds'), graph.get('FurinaPzbStart'))
    standing = graph.get('FurinaPzbStand')
    finish_at = choose('RecoverSeconds', standing, recovery.get_play_length(), .72)
    done = graph.branch('Evaluate', compare('Done', elapsed, finish_at))
    wire(step.find_then_pin(), done.find_execute_pin())

    def pulse(name, t, frequency, damping, scale):
        wave = math_(name + 'Wave', 'Sin', A=mul(name + 'AngularSpeed', t, frequency))
        decay = math_(name + 'Decay', 'Exp', A=mul(name + 'Damping', t, -damping))
        return mul(name + 'Result', mul(name + 'Envelope', wave, decay), scale)

    def ramp(name, a, b):
        alpha = math_(name + 'Clamp', 'FClamp', Value=mul(name + 'Normalize', sub(name + 'AfterStart', elapsed, a), 1./(b-a)), Min=0., Max=1.)
        return math_(name + 'Ease', 'FInterpEaseInOut', A=0., B=1., Alpha=alpha, Exponent=2.)

    initial = mul('SwingBack', sub('BackAndRelease', ramp('Back', .04, .56), ramp('Level', .62, 1.27)), 14.)
    look_down = mul('WatchFloor', sub('TransferGaze', ramp('FindHand', .97, 1.68), ramp('Horizon', 1.97, 3.12)), -38.)
    contact_time = math_('ImpactSince', 'FMax', A=0., B=sub('AfterImpact', elapsed, .66))
    eyes = add('GroundGaze', add('WholeArc', initial, look_down), pulse('Landing', contact_time, 38., 11., -4.5))
    lean = mul('RollWithBody', sub('TiltAndReturn', ramp('Tilt', .20, .75), ramp('UprightAgain', .86, 2.32)), -16.)
    braced_pitch = pulse('BracedHead', elapsed, 17., 8., 9.)
    braced_roll = pulse('BracedRoll', elapsed, 13., 9., -2.7)
    pitch = choose('Pitch', standing, eyes, braced_pitch)
    roll = choose('Roll', standing, lean, braced_roll)

    def orient(name, source, target_pitch, target_roll):
        original = value(graph, name + 'View', ENGINE + 'Controller:GetControlRotation', controller)
        current = graph.call(name + 'Axes', MATH + 'BreakRotator', InRot=original)
        pitch_delta = sub(name + 'PitchDelta', target_pitch, graph.get('FurinaPzbOldPitch'))
        roll_delta = sub(name + 'RollDelta', target_roll, graph.get('FurinaPzbOldRoll'))
        orientation = math_(name + 'Rotation', 'MakeRotator',
                            Pitch=add(name + 'AddPitch', current.find_output_pin('Pitch'), pitch_delta),
                            Yaw=current.find_output_pin('Yaw'),
                            Roll=add(name + 'AddRoll', current.find_output_pin('Roll'), roll_delta))
        rotate = graph.call(name + 'Apply', ENGINE + 'Controller:SetControlRotation', controller, NewRotation=orientation)
        return chain(source, [rotate,
                              graph.store(name + 'RememberPitch', 'FurinaPzbOldPitch', target_pitch),
                              graph.store(name + 'RememberRoll', 'FurinaPzbOldRoll', target_roll)])

    orient('Track', done.find_else_pin(), pitch, roll)
    zero = value(graph, 'Zero', SYSTEM + 'MakeLiteralDouble', Value=0.)
    finish = orient('Restore', done.find_then_pin(), zero, zero)
    clear = graph.call('StopEyes', SYSTEM + 'K2_ClearTimer', Object=owner, FunctionName=TICK)
    release = graph.store('Ready', 'FurinaPzbBusy', False)
    restore_body = graph.branch('WasStanding', standing)
    wire(chain(finish, [clear, release]), restore_body.find_execute_pin())
    locomotion = graph.call('RestoreLocomotion', ENGINE + 'SkeletalMeshComponent:SetAnimationMode', body,
                            InAnimationMode='AnimationBlueprint', bForceInitAnimScriptInstance=True)
    chain(restore_body.find_then_pin(), [locomotion, visibility('ShowViewmodel', True), ignore('UnlockMove', False)])


if __name__ == '__main__':
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.load_asset(PAWN)
    install(pawn)
    improve_floor_view(Graph(pawn))
    save(pawn)
    print('PZB39_BALANCE_SAVED')
