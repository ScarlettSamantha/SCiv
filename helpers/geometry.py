import math

from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, NodePath


def generate_flat_top_hex(radius: float = 1.0) -> NodePath:
    format = GeomVertexFormat.get_v3n3t2()
    vdata = GeomVertexData("hex", format, Geom.UH_static)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    texcoord = GeomVertexWriter(vdata, "texcoord")

    # Center vertex
    vertex.add_data3(0, 0, 0)  # type: ignore
    normal.add_data3(0, 0, 1)  # type: ignore
    texcoord.add_data2(0.5, 0.5)  # Center UV # type: ignore

    # Create outer 6 vertices
    for i in range(6):
        angle_deg = 60 * i - 30  # Flat-topped: rotate -30° for first corner
        angle_rad = math.radians(angle_deg)

        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)

        # Map to UV space: [-radius, +radius] → [0, 1]
        u = 0.5 + x / (2 * radius)
        v = 0.5 + y / (2 * radius)

        vertex.add_data3(x, y, 0)  # type: ignore
        normal.add_data3(0, 0, 1)  # type: ignore
        texcoord.add_data2(u, v)  # type: ignore

    # Create triangle fan from center to each edge
    tris = GeomTriangles(Geom.UH_static)
    for i in range(1, 7):
        a = 0  # center
        b = i
        c = 1 if i == 6 else i + 1
        tris.add_vertices(a, b, c)  # type: ignore

    geom = Geom(vdata)  # type: ignore
    geom.add_primitive(tris)  # type: ignore

    node = GeomNode("hex")
    node.add_geom(geom)  # type: ignore
    return NodePath(node)
