import bpy
import bmesh
import mathutils
from struct import pack

bone_names = (
    "PELVIS",
    "STOMACH",
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
bone_linkages = (0, 0, 1, 2, 2, 4, 5, 2, 7, 8, 0, 10, 11, 0, 13, 14)
bone_dict = {key: idx for idx, key in enumerate(bone_names)}


def save(context: bpy.types.Context, filepath: str):
    with open(filepath, "wb") as f:
        # Magic number
        f.write(b"CMod")
        # Version
        f.write(pack("<i", 2))

        depsgraph = context.evaluated_depsgraph_get()

        # Exit edit mode before exporting,
        # so current object states are exported properly.
        bpy.ops.object.mode_set(mode="OBJECT")

        cmc_verts = []
        cmc_uvs = []
        cmc_faces = []
        cmc_weights = []
        cmc_bones = []

        ob: bpy.types.Object = bpy.context.active_object
        if ob is None:
            return [True, "Select a mesh with an armature as its parent"]

        ob_for_convert: bpy.types.Object = ob.evaluated_get(depsgraph)
        parent_armature: bpy.types.Object = ob.parent

        if parent_armature is None:
            return [True, "Select a mesh with an armature as its parent"]
        if parent_armature.type != "ARMATURE":
            return [True, "Select a mesh with an armature as its parent"]
        parent_armature_data: bpy.types.Armature = parent_armature.data

        try:
            me: bpy.types.Mesh = ob_for_convert.to_mesh()
        except RuntimeError:
            me = None
        if me is None:
            return [True, "Select a mesh with an armature as its parent"]

        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)

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
                    face.verts[2].index,
                    face.verts[1].index,
                    face.verts[0].index,
                )
            )

        bm.free()

        pelvisBone: bpy.types.Bone = parent_armature_data.bones.get(bone_names[0])
        if pelvisBone is not None:
            cmc_bones.append([0.0, 0.0, 0.0])
            for boneIndex in range(1, 16):
                boneObject: bpy.types.Bone = parent_armature_data.bones.get(
                    bone_names[boneIndex]
                )
                lastBoneObject: bpy.types.Bone = parent_armature_data.bones.get(
                    bone_names[bone_linkages[boneIndex]]
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

                for index in range(16):
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
                        bone_names[index]
                    )
                    if boneObject is None:
                        finalWeightData.append([0.0, 0.0, 0.0, usingWeight])
                        continue

                    boneTransform: mathutils.Vector = (
                        boneObject.matrix_local.to_translation()
                    )
                    boneOffset: mathutils.Vector = (vert.co - boneTransform) / 1.125
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
