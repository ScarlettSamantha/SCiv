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


def generate_flat_top_hex_prism(
    radius: float = 1.0,
    height: float = 1.0,
    top_color: tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0),
    side_color: tuple[float, float, float, float] = (0.18, 0.18, 0.18, 1.0),
) -> NodePath:
    fmt = GeomVertexFormat.get_v3n3c4()
    vdata = GeomVertexData("hex_prism", fmt, Geom.UH_static)

    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")

    top_vertices: list[tuple[float, float]] = []
    for index in range(6):
        angle = math.radians(60 * index - 30)
        top_vertices.append((radius * math.cos(angle), radius * math.sin(angle)))

    vw.add_data3(0, 0, height)
    nw.add_data3(0, 0, 1)
    cw.add_data4f(*top_color)

    for x, y in top_vertices:
        vw.add_data3(x, y, height)
        nw.add_data3(0, 0, 1)
        cw.add_data4f(*top_color)

    tris = GeomTriangles(Geom.UH_static)
    for index in range(1, 7):
        next_index = 1 if index == 6 else index + 1
        tris.add_vertices(0, index, next_index)

    for index in range(6):
        next_index = (index + 1) % 6
        x0, y0 = top_vertices[index]
        x1, y1 = top_vertices[next_index]
        nx = (x0 + x1) * 0.5
        ny = (y0 + y1) * 0.5
        length = math.hypot(nx, ny) or 1.0
        normal = (nx / length, ny / length, 0.0)

        base_index = vdata.get_num_rows()

        for x, y, z in (
            (x0, y0, 0.0),
            (x1, y1, 0.0),
            (x1, y1, height),
            (x0, y0, height),
        ):
            vw.add_data3(x, y, z)
            nw.add_data3(*normal)
            cw.add_data4f(*side_color)

        tris.add_vertices(base_index, base_index + 1, base_index + 2)
        tris.add_vertices(base_index, base_index + 2, base_index + 3)

    geom = Geom(vdata)
    geom.add_primitive(tris)

    node = GeomNode("hex_prism")
    node.add_geom(geom)
    return NodePath(node)


