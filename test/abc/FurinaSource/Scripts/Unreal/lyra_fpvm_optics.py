"""Wire the repaired viewmodels, screen-space alignment and three optical views."""
import json
import math
import uuid
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
PAWN = '/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP'
HUD = '/Game/Furina/FP/BP_FurinaHUD'
ENGINE = '/Script/Engine.'
MATH = ENGINE + 'KismetMathLibrary:'
STRINGS = ENGINE + 'KismetStringLibrary:'
SCOPE_ASSETS = {'kar98k_zf39': ('Kar98k', 'ZF39'), 'kar98k_zf41': ('Kar98k', 'ZF41'), 'g43_zf4': ('G43', 'ZF4')}
VARIANTS = json.loads((ROOT / 'FurinaSource' / 'Data' / 'fpvm_view_alignment.json').read_text(encoding='utf-8'))


def wire(source, destination):
    assert source.is_valid() and destination.is_valid()
    assert unreal.BlueprintGraphPinLibrary.try_create_connection(source, destination)


def relay(start, first, end):
    """Insert one exec chain after a node and keep every existing continuation."""
    downstream = list(start.list_connected_pins())
    start.break_pin_links()
    wire(start, first)
    for destination in downstream:
        wire(end, destination)


def literal(node, name, value):
    if isinstance(value, unreal.Object):
        value = value.get_path_name()
    if isinstance(value, bool):
        value = str(value).lower()
    assert node.find_input_pin(name).set_pin_value(str(value)), (node.get_name(), name, value)


class Graph:
    def __init__(self, blueprint, prefix='ScopeView_'):
        self.blueprint = blueprint
        self.editor = unreal.BlueprintGraphEditor.get_graph_editor_by_name(blueprint, 'EventGraph')
        self.nodes = {n.get_name(): n for n in self.editor.list_all_nodes()}
        self.prefix = prefix

    def call(self, name, function, target=None, **inputs):
        node = self.editor.add_call_function_node(function)
        assert node, function
        node.rename(self.prefix + name)
        if target is not None:
            wire(target, node.find_self_pin())
        for key, value in inputs.items():
            if isinstance(value, unreal.BlueprintGraphPin):
                wire(value, node.find_input_pin(key))
            else:
                literal(node, key, value)
        return node

    def get(self, variable, owner=None, source=None):
        node = self.editor.add_get_member_variable_node(variable, owner or '')
        assert node, variable
        if source is not None:
            wire(source, node.find_self_pin())
        return node.find_output_pin(variable)

    def store(self, name, variable, value):
        node = self.editor.add_set_member_variable_node(variable)
        assert node, variable
        node.rename(self.prefix + name)
        if isinstance(value, unreal.BlueprintGraphPin):
            wire(value, node.find_input_pin(variable))
        else:
            literal(node, variable, value)
        return node

    def branch(self, name, value):
        node = self.editor.add_branch_node()
        node.rename(self.prefix + name)
        wire(value, node.find_input_pin('Condition'))
        return node

    def locate(self, prefix):
        return next(node for name, node in self.nodes.items() if name.startswith(prefix))


def chain(source, nodes):
    for node in nodes:
        wire(source, node.find_execute_pin())
        source = node.find_then_pin()
    return source


def view_transform(key):
    data = VARIANTS[key]
    rotation = unreal.Quat(*data['ue_quat_xyzw']).rotator()
    location = ','.join(str(n) for n in data['ue_loc_cm'])
    return location, f'{rotation.pitch},{rotation.yaw},{rotation.roll}'


def update_iron_sight_transforms(pawn):
    graph = Graph(pawn)
    for key, loc_name, rot_name in (('kar98k', 'VW_S_22_', 'VW_S_23_'), ('g43', 'VW_S_39_', 'VW_S_40_')):
        loc, rot = view_transform(key)
        literal(graph.locate(loc_name), 'FurinaVMAdsLoc', loc)
        literal(graph.locate(rot_name), 'FurinaVMAdsRot', rot)


def optic_material(scope):
    folder = '/Game/Furina/FPVM'
    name = 'M_FPVM_View_' + scope
    path = f'{folder}/{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    edit = unreal.MaterialEditingLibrary
    uv = edit.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -600, 0)
    size = edit.create_material_expression(material, unreal.MaterialExpressionViewSize, -600, 180)
    shape = edit.create_material_expression(material, unreal.MaterialExpressionCustom, -270, 0)
    shape.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    inputs = [unreal.CustomInput(), unreal.CustomInput()]
    inputs[0].set_editor_property('input_name', 'UV')
    inputs[1].set_editor_property('input_name', 'Viewport')
    shape.set_editor_property('inputs', inputs)
    radius, span, width, post = {'ZF39': (.42, .026, .002, .013), 'ZF41': (.34, .036, .0015, .010), 'ZF4': (.41, .025, .0017, .011)}[scope]
    shape.set_editor_property('code', f'''
float2 p = UV - 0.5;
p.x *= Viewport.x / max(Viewport.y, 1);
float r = length(p);
float px = 1.1 / max(Viewport.y, 1);
float body = smoothstep({radius} - px, {radius} + px, r);
float line = (1 - smoothstep({width}, {width} + px, abs(p.y))) * smoothstep({span}-px,{span}+px,abs(p.x));
float tapered = {post} * saturate(p.y / 0.065);
float point = (1 - smoothstep(tapered, tapered + px, abs(p.x))) * smoothstep(0,px,p.y);
float rim = 0.25 * smoothstep({radius} - 0.04, {radius}, r);
return saturate(max(max(body,line),max(point,rim)));
''')
    black = edit.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -270, 200)
    black.set_editor_property('constant', unreal.LinearColor(.002, .003, .004, 1))
    assert edit.connect_material_expressions(uv, '', shape, 'UV')
    assert edit.connect_material_expressions(size, '', shape, 'Viewport')
    assert edit.connect_material_property(shape, '', unreal.MaterialProperty.MP_OPACITY)
    assert edit.connect_material_property(black, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    return material


def configure_viewmodels(pawn):
    graph = Graph(pawn)
    if 'ScopeView_SetCamera' in graph.nodes:
        return
    partial = [node for name, node in graph.nodes.items() if name.startswith('ScopeView_')]
    if partial:
        for node in partial:
            node.rename('Discarded_' + uuid.uuid4().hex)
        graph.editor.remove_nodes(partial)
        wire(graph.locate('VW_S_7_').find_then_pin(), graph.locate('VW_Br_10_').find_execute_pin())
        graph = Graph(pawn)
    vm = graph.get('FurinaFPVM')
    key = graph.get('FurinaPrimaryKey')
    # Optional optic keys are normal primary selections and reuse their rifle animation clips.
    start = graph.locate('VW_S_7_').find_then_pin()
    fallback = list(start.list_connected_pins())
    defaults = {}
    for family, ref in (('kar98k', 'Kar98k'), ('g43', 'G43')):
        defaults[family] = unreal.load_asset(f'/Game/Furina/FPVM/{ref}/SK_FPVM_{ref}_Interior')
        select = graph.locate(f'VW_Mesh_{family}_')
        select.find_input_pin('NewMesh').break_pin_links()
        literal(select, 'NewMesh', defaults[family])
    reset_zoom = graph.store('Reset', 'FurinaScopeZoom', 1.)
    reset_material = graph.store('ClearOptic', 'FurinaScopeOverlay', 'None')
    start.break_pin_links()
    tail = chain(start, [reset_zoom, reset_material])
    for item, (model, optic) in SCOPE_ASSETS.items():
        base = item.rsplit('_', 1)[0]
        match = graph.call(f'Key_{optic}', STRINGS + 'EqualEqual_StrStr', A=key, B=item)
        branch = graph.branch(f'Is_{optic}', match.find_result_pin())
        wire(tail, branch.find_execute_pin())
        mesh = unreal.load_asset(f'/Game/Furina/FPVM/{model}/SK_FPVM_{model}_{optic}')
        assert mesh, optic
        equip = graph.call(f'Mesh_{optic}', ENGINE + 'SkeletalMeshComponent:SetSkeletalMeshAsset', vm, NewMesh=mesh)
        clear_overrides = [graph.call(f'Clear_{optic}_{slot}', ENGINE + 'PrimitiveComponent:SetMaterial', vm, ElementIndex=slot) for slot in range(10)]
        items = [equip, *clear_overrides]
        for animation in ('Idle', 'Fire', 'Reload'):
            items.append(graph.store(f'{animation}_{optic}', 'FurinaVMAnim' + animation, graph.get(f'FurinaVM{animation}_{base}')))
        loc, rot = view_transform(item)
        items.extend([
            graph.store('Loc_' + optic, 'FurinaVMAdsLoc', loc),
            graph.store('Rot_' + optic, 'FurinaVMAdsRot', rot),
            graph.store('Power_' + optic, 'FurinaScopeZoom', VARIANTS[item]['magnification']),
            graph.store('Mask_' + optic, 'FurinaScopeOverlay', optic_material(optic)),
            graph.store('FireTime_' + optic, 'FurinaVMFireLen', 1.2 if base == 'kar98k' else .25),
            graph.store('ReloadTime_' + optic, 'FurinaVMReloadLen', 3.2 if base == 'kar98k' else 5.9),
            graph.store('Valid_' + optic, 'FurinaVMValid', True),
        ])
        wire(chain(branch.find_then_pin(), items), graph.locate('VM_Br_12_').find_execute_pin())
        tail = branch.find_else_pin()
    for target in fallback:
        wire(tail, target)

    # Existing non-optic ADS is 60 degrees. Compute focal length ratios for zoom.
    power = graph.get('FurinaScopeZoom')
    is_optic = graph.call('HasZoom', MATH + 'Greater_DoubleDouble', A=power)
    one = graph.call('One', ENGINE + 'KismetSystemLibrary:MakeLiteralDouble', Value=1.)
    wire(one.find_result_pin(), is_optic.find_input_pin('B'))
    eligible = graph.call('ValidZoom', MATH + 'BooleanAND', A=is_optic.find_result_pin(), B=graph.get('FurinaVMOn'))
    aiming = graph.nodes['K2Node_FPT_AdsOnT'].find_result_pin()
    aiming_with_optic = graph.call('Aiming', MATH + 'BooleanAND', A=eligible.find_result_pin(), B=aiming)
    not_reloading = graph.call('NotReloading', MATH + 'Not_PreBool', A=graph.get('FurinaReloading'))
    zoom_visible = graph.call('CanDraw', MATH + 'BooleanAND', A=aiming_with_optic.find_result_pin(), B=not_reloading.find_result_pin())
    setter = graph.store('SetActive', 'FurinaScopeActive', zoom_visible.find_result_pin())
    visibility = graph.call('HideViewmodel', ENGINE + 'SceneComponent:SetHiddenInGame', vm, NewHidden=zoom_visible.find_result_pin())
    is4x = graph.call('HighPower', MATH + 'Greater_DoubleDouble', A=power)
    two = graph.call('Two', ENGINE + 'KismetSystemLibrary:MakeLiteralDouble', Value=2.)
    wire(two.find_result_pin(), is4x.find_input_pin('B'))
    fovs = [math.degrees(2 * math.atan(math.tan(math.radians(30)) / m)) for m in (4, 1.5)]
    field = graph.call('PickFOV', MATH + 'SelectFloat', bPickA=is4x.find_result_pin(), A=fovs[0], B=fovs[1])
    legacy_field = graph.call('StandardFOV', MATH + 'SelectFloat', bPickA=aiming, A=60., B=85.)
    using_scope = graph.call('FinalFOV', MATH + 'SelectFloat', bPickA=zoom_visible.find_result_pin(), A=field.find_result_pin(), B=legacy_field.find_result_pin())
    set_camera = graph.call('SetCamera', ENGINE + 'CameraComponent:SetFieldOfView', graph.get('FPCamera'), InFieldOfView=using_scope.find_result_pin())
    relay(graph.nodes['TFP_SetArm'].find_then_pin(), setter.find_execute_pin(), set_camera.find_then_pin())
    chain(setter.find_then_pin(), [visibility, set_camera])


def configure_hud(hud, pawn_class):
    graph = Graph(hud)
    if 'ScopeView_DrawReticle_ZF4' in graph.nodes:
        return
    player = next(pin for pin in graph.nodes['M4HUD_Cast'].list_output_pins() if str(pin.get_pin_name()).startswith('As'))
    key = pawn_class.get_path_name()
    active = graph.nodes.get('ScopeView_HasGlass')
    if active:
        active.find_then_pin().break_pin_links()
        obsolete = [node for name, node in graph.nodes.items()
                    if name.startswith('ScopeView_') and node != active]
        for node in obsolete:
            node.rename('Discarded_' + uuid.uuid4().hex)
        graph.editor.remove_nodes(obsolete)
    else:
        active = graph.branch('HasGlass', graph.get('FurinaScopeActive', key, player))
        wire(graph.nodes['HistoricalView_DrawOnlyLegacy'].find_then_pin(), active.find_execute_pin())

    draw = graph.nodes['K2Node_FPAH_Draw']
    width = draw.find_output_pin('SizeX')
    height = draw.find_output_pin('SizeY')
    def math_value(name, function, a, b):
        return graph.call(name, MATH + function, A=a, B=b).find_result_pin()

    side = math_value('SquareSize', 'FMin', width, height)
    x = math_value('SquareX', 'Multiply_DoubleDouble', math_value('HorizontalRemainder', 'Subtract_DoubleDouble', width, side), .5)
    y = math_value('SquareY', 'Multiply_DoubleDouble', math_value('VerticalRemainder', 'Subtract_DoubleDouble', height, side), .5)
    right = math_value('SquareRight', 'Add_DoubleDouble', x, side)
    bottom = math_value('SquareBottom', 'Add_DoubleDouble', y, side)
    matte = graph.call('MatteTint', MATH + 'MakeColor', R=.002, G=.002, B=.003, A=1.).find_result_pin()
    white = graph.call('ReticleTint', MATH + 'MakeColor', R=1., G=1., B=1., A=1.).find_result_pin()
    black = [
        graph.call('MaskLeft', ENGINE + 'HUD:DrawRect', RectColor=matte, ScreenW=x, ScreenH=height),
        graph.call('MaskRight', ENGINE + 'HUD:DrawRect', RectColor=matte, ScreenX=right, ScreenW=x, ScreenH=height),
        graph.call('MaskTop', ENGINE + 'HUD:DrawRect', RectColor=matte, ScreenX=x, ScreenW=side, ScreenH=y),
        graph.call('MaskBottom', ENGINE + 'HUD:DrawRect', RectColor=matte, ScreenX=x, ScreenY=bottom, ScreenW=side, ScreenH=y),
    ]
    tail = chain(active.find_then_pin(), black)
    weapon = graph.get('FurinaPrimaryKey', key, player)
    for item, (_family, optic) in SCOPE_ASSETS.items():
        match = graph.call('SelectReticle_' + optic, STRINGS + 'EqualEqual_StrStr', A=weapon, B=item)
        branch = graph.branch('Reticle_' + optic, match.find_result_pin())
        texture = scope_texture(optic)
        paint = graph.call('DrawReticle_' + optic, ENGINE + 'HUD:DrawTexture', Texture=texture, ScreenX=x, ScreenY=y,
                            ScreenW=side, ScreenH=side, TextureUWidth=1., TextureVHeight=1.,
                            TintColor=white, BlendMode='BLEND_Translucent', Scale=1.)
        wire(tail, branch.find_execute_pin())
        wire(branch.find_then_pin(), paint.find_execute_pin())
        tail = branch.find_else_pin()


def scope_texture(optic):
    name = 'T_FPVM_View_' + optic
    folder = '/Game/Furina/FPVM'
    path = f'{folder}/{name}'
    assets = unreal.EditorAssetLibrary
    if not assets.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'FurinaSource' / 'Textures' / 'FPVM' / (name + '.png'))
        task.destination_path = folder
        task.destination_name = name
        task.automated = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(path)
    assert texture, path
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    assert assets.save_loaded_asset(texture, False)
    return texture


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(), 'End PIE before editing assets'
    pawn = unreal.load_asset(PAWN)
    hud = unreal.load_asset(HUD)
    api = unreal.BlueprintEditorLibrary
    existing = {str(name) for name in api.list_member_variable_names(pawn)}
    fields = {'FurinaScopeZoom': api.get_basic_type_by_name('real'), 'FurinaScopeActive': api.get_basic_type_by_name('bool'),
              'FurinaScopeOverlay': api.get_object_reference_type(unreal.MaterialInterface)}
    for name, field in fields.items():
        if name not in existing:
            assert api.add_member_variable(pawn, name, field), name
    configure_viewmodels(pawn)
    update_iron_sight_transforms(pawn)
    api.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    configure_hud(hud, pawn.generated_class())
    api.compile_blueprint(hud)
    assert hud.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    for asset in (pawn, hud):
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False), asset.get_name()
    print('FPVM_OPTICS_SAVED')


if __name__ == '__main__':
    main()
