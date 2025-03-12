import bpy
import mathutils
from typing import Optional

armature_root = mathutils.Vector((0.0, 0.0625, -0.1875))
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


def load_mesh(
    context: bpy.types.Context,
    name: str,
    vertices: list[tuple[float, float, float]],
    faces,
    vertex_uvs,
    vertex_weights,
    bones: Optional[list[tuple[float, float, float]]],
):
    new_vertices: list[tuple[float, float, float]] = []
    for vertex in vertices:
        new_vertices.append((vertex[0], vertex[2], vertex[1]))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(new_vertices, (), faces)

    if vertex_uvs:
        layer = mesh.uv_layers.new(do_init=True)
        for loop in mesh.loops:
            layer.uv[loop.index].vector = mathutils.Vector(
                vertex_uvs[loop.vertex_index]
            )

    obj = bpy.data.objects.new(name, mesh)

    armatureSpaceBonePositions = [None] * 16
    if bones:
        boneObjects: list[bpy.types.EditBone] = []

        bpy.ops.object.armature_add(
            enter_editmode=True, align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
        )
        armature_object: bpy.types.Object = bpy.context.active_object
        armature: bpy.types.Armature = armature_object.data

        # set up the root pelvis bone
        armature.edit_bones[0].name = "PELVIS"
        armature.edit_bones[0].head = armature_root
        armature.edit_bones[0].length = 0.2
        armatureSpaceBonePositions[0] = armature_root
        boneObjects.append(armature.edit_bones[0])

        # parent the mesh object to the armature and give it an armature deform
        obj.parent = armature_object
        obj.parent_type = "ARMATURE"

        # set up editbones, skipping pelvis
        for bone_index in range(1, 16):
            linkedBoneIdx = bone_linkages[bone_index]
            fileBonePos = mathutils.Vector(bones[bone_index])
            bonePos = (
                mathutils.Vector((fileBonePos.x, fileBonePos.z, fileBonePos.y)) * 1.125
            )
            lastBonePos = armatureSpaceBonePositions[linkedBoneIdx]

            editBone = armature.edit_bones.new(bone_names[bone_index])
            editBone.parent = boneObjects[linkedBoneIdx]
            editBone.matrix = mathutils.Matrix.Translation(
                lastBonePos
            ) @ mathutils.Matrix.Translation(bonePos)
            editBone.tail = boneObjects[linkedBoneIdx].head

            boneObjects.append(editBone)
            armatureSpaceBonePositions[bone_index] = lastBonePos + bonePos

        if vertex_weights:
            vertexGroups: list[bpy.types.VertexGroup] = []

            for bone_index in range(0, 16):
                vertexGroups.append(obj.vertex_groups.new(name=bone_names[bone_index]))
            for index, weights in enumerate(vertex_weights):
                weightIndices: list[int] = [0] * 4
                weightValues: list[float] = [1.0, 0.0, 0.0, 0.0]
                weightOffsets: list[mathutils.Vector] = []
                weightCount = 0
                for boneIndex, innerWeights in enumerate(weights):
                    if weightCount >= 4:
                        break
                    if innerWeights[3] <= 0.0:
                        continue

                    weightIndices[weightCount] = boneIndex
                    weightValues[weightCount] = innerWeights[3]
                    weightOffset = (
                        mathutils.Vector(
                            (innerWeights[0], innerWeights[2], innerWeights[1])
                        )
                        * 1.125
                    )
                    weightOffsets.append(weightOffset)

                    weightCount += 1

                newVertPosition = mathutils.Vector((0, 0, 0))
                for weightIndex, indice in enumerate(weightIndices):
                    if weightValues[weightIndex] <= 0.0:
                        break
                    vertexGroups[indice].add(
                        [index], weightValues[weightIndex], "REPLACE"
                    )
                    newVertPosition += (
                        weightOffsets[weightIndex] + armatureSpaceBonePositions[indice]
                    ) * weightValues[weightIndex]

                if weightCount > 0:
                    mesh.vertices[index].co = newVertPosition

        armature_modifier: bpy.types.ArmatureModifier = obj.modifiers.new(
            "Armature", "ARMATURE"
        )
        armature_modifier.object = armature_object

    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")

    view_layer = context.view_layer
    collection = view_layer.active_layer_collection.collection

    collection.objects.link(obj)
    obj.select_set(True)

    view_layer.update()
