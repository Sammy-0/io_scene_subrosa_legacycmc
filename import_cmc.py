import bpy
from struct import unpack
from . import shared


def load(context, filepath):
    with open(filepath, "rb") as f:
        f.read(4)  # Magic number

        (version,) = unpack("<i", f.read(4))
        assert version == 2, "Unknown file version."

        vertices = []
        faces = []
        vertex_uvs = []
        vertex_weights = []
        bones = []

        (bone_count,) = unpack("<i", f.read(4))
        for _ in range(bone_count):
            bones.append(unpack("<fff", f.read(4 * 3)))

        (vertex_count,) = unpack("<i", f.read(4))
        for _ in range(vertex_count):
            weights = []
            vertices.append(unpack("<fff", f.read(4 * 3)))
            for _ in range(bone_count):
                weights.append(unpack("<ffff", f.read(4 * 4)))

            vertex_uvs.append(unpack("<ff", f.read(4 * 2)))
            vertex_weights.append(weights)

        (face_count,) = unpack("<i", f.read(4))
        for _ in range(face_count):
            vertex_indices = unpack("<iii", f.read(4 * 3))
            faces.append(tuple(vertex_indices[:]))

        name = bpy.path.display_name_from_filepath(filepath)
        shared.load_mesh(
            context, name, vertices, faces, vertex_uvs, vertex_weights, bones
        )

    return {"FINISHED"}
