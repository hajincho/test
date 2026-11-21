"""Extract one visual round from the project's clip mesh for loose reloads."""
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    model = rig.load_weapon('mauser_clip')
    mesh = bmesh.new()
    mesh.from_mesh(model.data)
    materials = [slot.name for slot in model.data.materials]
    other = [face for face in mesh.faces if materials[face.material_index] not in ('6.5', 'case') or face.calc_center_median().z < 2.02]
    bmesh.ops.delete(mesh, geom=other, context='FACES')
    bmesh.ops.delete(mesh, geom=[vertex for vertex in mesh.verts if not vertex.link_faces], context='VERTS')
    assert mesh.faces
    mesh.to_mesh(model.data)
    mesh.free()
    # Match the orientation of the first-person rig's existing animated prop socket.
    # 2026-11-21: 예전 Z 90° 회전은 소켓(VM_Clip 뼈) 기준으로 탄이 90.2° 옆으로 누운 원인이었음.
    # UE 의 VM_Clip 참조 포즈(Data/fpvm_refpose.json)로 계산한 변환(Data/fpvm_round_fix.json, 클립 맨 위 탄 자리와 일치).
    # 소켓에 SnapToTarget + 상대 크기 0.01 로 붙으므로: UE 정점 v = P @ n(원본 cm) -> Blender 데이터 = 0.01 * diag(1,-1,1) @ P @ n
    import json as _json
    P = Matrix(_json.load(open(Path(rig.D) / 'Data' / 'fpvm_round_fix.json'))['Kar98k']['P_needed'])
    M3 = Matrix.Diagonal((1, -1, 1)) @ P
    model.data.transform(Matrix.Scale(.01, 4) @ M3.to_4x4())
    if M3.determinant() < 0: model.data.flip_normals()
    for material in model.data.materials:
        if material and material.name in ('6.5', 'case'):
            material.name = {'6.5': 'Clip_Projectile', 'case': 'Clip_Case'}[material.name]
    bpy.ops.object.select_all(action='DESELECT')
    model.select_set(True)
    bpy.context.view_layer.objects.active = model
    path = Path(rig.D) / 'FBX' / 'FPVM' / 'SM_FPVM_LooseRound.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'}, bake_anim=False,
                             axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', path_mode='STRIP')


if __name__ == '__main__':
    main()
