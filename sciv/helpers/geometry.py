import math

from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, NodePath


def generate_flat_top_hex(
    radius: float = 1.0,
    inner_color: tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1),
    border_color: tuple[float, float, float, float] = (1, 0, 0, 1),
) -> NodePath:
    # use a format with positions, normals, colors, and texcoords
    fmt = GeomVertexFormat.get_v3n3c4t2()
    vdata = GeomVertexData("hex", fmt, Geom.UH_static)

    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tw = GeomVertexWriter(vdata, "texcoord")

    # 1) Center vertex
    vw.add_data3(0, 0, 0)
    nw.add_data3(0, 0, 1)
    cw.add_data4f(*inner_color)
    tw.add_data2(0.5, 0.5)

    # 2) Outer ring
    for i in range(6):
        ang = math.radians(60 * i - 30)
        x, y = radius * math.cos(ang), radius * math.sin(ang)
        u, v = 0.5 + x / (2 * radius), 0.5 + y / (2 * radius)

        vw.add_data3(x, y, 0)
        nw.add_data3(0, 0, 1)
        cw.add_data4f(*border_color)
        tw.add_data2(u, v)

    # 3) Triangle fan
    tris = GeomTriangles(Geom.UH_static)
    for i in range(1, 7):
        a = 0
        b = i
        c = 1 if i == 6 else i + 1
        tris.add_vertices(a, b, c)

    geo = Geom(vdata)
    geo.add_primitive(tris)

    node = GeomNode("hex")
    node.add_geom(geo)
    return NodePath(node)
