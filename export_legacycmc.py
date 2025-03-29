import bpy
import bmesh
import mathutils
from struct import pack

legacy_bone_names = (
    "PELVIS",
    "TORSO",
    "HEAD",
    "LEFTSHOULDER",
    "LEFTFOREARM",
    "LEFTHAND",
    "RIGHTSHOULDER",
    "RIGHTFOREARM",
    "RIGHTHAND",
    "LEFTTHIGH",
    "LEFTSHIN",
    "LEFTFOOT",
    "RIGHTTHIGH",
    "RIGHTSHIN",
    "RIGHTFOOT",
)
legacy_bone_linkages = (0, 0, 1, 1, 3, 4, 1, 6, 7, 0, 9, 10, 0, 12, 13)
bone_dict = {key: idx for idx, key in enumerate(legacy_bone_names)}


# Taken from https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin
def split_multi_uv_vertices(
    context: bpy.types.Context, mesh: bpy.types.Mesh, b_mesh: bmesh.types.BMesh
):
    b_mesh.verts.ensure_lookup_table()

    for ver in b_mesh.verts:
        ver.select_set(False)

    for i, uv_layer in enumerate(mesh.uv_layers):
        tx_coords = [None] * len(uv_layer.data)
        for j, face in enumerate(b_mesh.faces):
            for loop in face.loops:
                vert_index = mesh.polygons[j].vertices[loop.index % 3]
                if tx_coords[vert_index] is None:
                    tx_coords[vert_index] = uv_layer.data[loop.index].uv
                elif tx_coords[vert_index] != uv_layer.data[loop.index].uv:
                    b_mesh.verts[vert_index].select_set(True)
                    vert_index2 = mesh.polygons[j].vertices[(loop.index + 1) % 3]
                    b_mesh.verts[vert_index2].select_set(True)
                    vert_index3 = mesh.polygons[j].vertices[(loop.index - 1) % 3]
                    b_mesh.verts[vert_index3].select_set(True)

    split_edges = [e for e in b_mesh.edges if e.verts[0].select and e.verts[1].select]

    if len(split_edges) > 0:
        bmesh.ops.split_edges(b_mesh, edges=split_edges)

    return b_mesh


def save(context: bpy.types.Context, filepath: str):
    # Exit edit mode before exporting,
    # so current object states are exported properly.
    bpy.ops.object.mode_set(mode="OBJECT")

    depsgraph = context.evaluated_depsgraph_get()
    ob: bpy.types.Object = bpy.context.active_object
    if ob is None or ob.type != "MESH":
        return [True, "Select a mesh with an armature as its parent"]

    ob_for_convert: bpy.types.Object = ob.evaluated_get(depsgraph)
    if ob_for_convert is None:
        return [True, "Select a mesh with an armature as its parent"]

    parent_armature: bpy.types.Object = ob.parent
    if parent_armature is None or parent_armature.type != "ARMATURE":
        return [True, "Select a mesh with an armature as its parent"]
    if parent_armature.type != "ARMATURE":
        return [True, "Select a mesh with an armature as its parent"]
    parent_armature_data: bpy.types.Armature = parent_armature.data

    me: bpy.types.Mesh = ob_for_convert.data
    if me.id_type != "MESH":
        return [True, "Select a mesh with an armature as its parent"]

    with open(filepath, "wb") as f:
        # Magic number
        f.write(b"CMod")
        # Version
        f.write(pack("<i", 2))

        cmc_verts = []
        cmc_uvs = []
        cmc_faces = []
        cmc_weights = []
        cmc_bones = []

        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        me.update()

        bm = bmesh.new()
        bm.from_mesh(me)
        bm = split_multi_uv_vertices(context, me, bm)
        bm.to_mesh(me)
        me.update()

        uv_layer = bm.loops.layers.uv.verify()

        for vertex in bm.verts:
            cmc_verts.append(vertex.co[:])
            loops = vertex.link_loops
            if len(loops) > 0:
                uv_data = loops[0][uv_layer]
                cmc_uvs.append(uv_data.uv[:])
            else:
                cmc_uvs.append((0.0, 0.0))

        for face in bm.faces:
            cmc_faces.append(
                (
                    face.verts[0].index,
                    face.verts[1].index,
                    face.verts[2].index,
                )
            )

        bm.free()

        pelvisBone: bpy.types.Bone = parent_armature_data.bones.get(legacy_bone_names[0])
        if pelvisBone is not None:
            cmc_bones.append([0.0, 0.0, 0.0])
            for boneIndex in range(1, 15):
                boneObject: bpy.types.Bone = parent_armature_data.bones.get(
                    legacy_bone_names[boneIndex]
                )
                lastBoneObject: bpy.types.Bone = parent_armature_data.bones.get(
                    legacy_bone_names[legacy_bone_linkages[boneIndex]]
                )
                if (boneObject is None) or (lastBoneObject is None):
                    continue

                boneTransform: mathutils.Matrix = boneObject.matrix_local
                lastBoneTransform: mathutils.Matrix = lastBoneObject.matrix_local
                boneOffset: mathutils.Vector = (
                    boneTransform.to_translation() - lastBoneTransform.to_translation()
                ) / 1.125

                cmc_bones.append(boneOffset[:])

            for vert in me.vertices:
                vert: bpy.types.MeshVertex
                weightIndices: list[int] = [0] * 4
                weightValues: list[float] = [1.0, 0.0, 0.0, 0.0]
                finalWeightData = []

                groupCount = 0
                for group in vert.groups:
                    group: bpy.types.VertexGroupElement
                    if groupCount >= 4:
                        break
                    if group.weight <= 0.0:
                        continue

                    realGroup: bpy.types.VertexGroup = ob_for_convert.vertex_groups[
                        group.group
                    ]
                    realGroupName: str = realGroup.name
                    realGroupIndex: int = bone_dict.get(realGroupName)
                    if realGroupIndex is None:
                        continue

                    weightIndices[groupCount] = realGroupIndex
                    weightValues[groupCount] = group.weight

                    groupCount += 1

                for index in range(15):
                    usingIndice = None
                    try:
                        usingIndice = weightIndices.index(index)
                    except ValueError:
                        finalWeightData.append([0.0] * 4)
                        continue

                    usingWeight = weightValues[usingIndice]
                    if usingWeight <= 0.0:
                        finalWeightData.append([0.0] * 4)
                        continue

                    boneObject: bpy.types.Bone = parent_armature_data.bones.get(
                        legacy_bone_names[index]
                    )
                    if boneObject is None:
                        finalWeightData.append([0.0, 0.0, 0.0, usingWeight])
                        continue

                    boneTransform: mathutils.Vector = (
                        boneObject.matrix_local.to_translation()
                    )
                    boneOffset: mathutils.Vector = (vert.co - boneTransform) / 1.125

                    # If there is no loaded weights, offset will be 0
                    if groupCount <= 0:
                        boneOffset = mathutils.Vector()

                    finalWeightData.append(
                        [boneOffset.x, boneOffset.y, boneOffset.z, usingWeight]
                    )

                cmc_weights.append(finalWeightData)

        f.write(pack("<i", len(cmc_bones)))
        for bone in cmc_bones:
            x, z, y = bone
            f.write(pack("<fff", x, y, z))

        f.write(pack("<i", len(cmc_verts)))
        for i in range(len(cmc_verts)):
            x, z, y = cmc_verts[i]
            f.write(pack("<fff", x, y, z))
            for weight in cmc_weights[i]:
                xw, zw, yw, w = weight
                f.write(pack("<ffff", xw, yw, zw, w))
            u, v = cmc_uvs[i]
            f.write(pack("<ff", u, v))

        f.write(pack("<i", len(cmc_faces)))
        for face in cmc_faces:
            f.write(pack("<iii", *face))

    return [False, None]
