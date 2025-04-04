import bpy
import bmesh
from struct import pack


def save(context: bpy.types.Context, filepath: str):
    with open(filepath, "wb") as f:
        # Magic number
        f.write(b"CMod")
        # Version
        f.write(pack("<i", 3))

        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene

        # Exit edit mode before exporting,
        # so current object states are exported properly.
        bpy.ops.object.mode_set(mode="OBJECT")

        cmo_verts = []
        cmo_uvs = []
        cmo_faces = []

        for ob in scene.objects:
            ob_for_convert = ob.evaluated_get(depsgraph)

            try:
                me = ob_for_convert.to_mesh()
            except RuntimeError:
                me = None

            if me is None:
                continue

            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.triangulate(bm, faces=bm.faces)

            uv_layer = bm.loops.layers.uv.verify()

            for vertex in bm.verts:
                cmo_verts.append(vertex.co[:])
                loops = vertex.link_loops
                if len(loops) > 0:
                    uv_data = loops[0][uv_layer]
                    cmo_uvs.append(uv_data.uv[:])
                else:
                    cmo_uvs.append((0.0, 0.0))

            for face in bm.faces:
                cmo_faces.append(
                    (
                        face.verts[0].index,
                        face.verts[1].index,
                        face.verts[2].index,
                    )
                )

            bm.free()

        f.write(pack("<i", len(cmo_verts)))

        for i in range(len(cmo_verts)):
            x, z, y = cmo_verts[i]
            f.write(pack("<fff", x, y, z))
            u, v = cmo_uvs[i]
            f.write(pack("<fff", u, v, 0.0))

        f.write(pack("<i", len(cmo_faces)))

        for face in cmo_faces:
            f.write(pack("<i", 3))
            f.write(pack("<iii", *face))
            f.write(pack("<ii", 0, 0))

    return {"FINISHED"}
