from typing import TYPE_CHECKING, List, Tuple
from panda3d.core import (
    Geom,
    GeomNode,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    GeomTriangles,
    NodePath,
    Shader,
)
import math

from helpers.colors import Colors, Tuple4f

if TYPE_CHECKING:
    from managers.entity import BaseTile

if TYPE_CHECKING:
    pass


# GLSL shaders with flat qualifier for uniform tile color
VERT_SHADER = """
#version 130
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 v_normal;
flat out vec4 v_color;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = normalize(p3d_Normal);
    v_color = p3d_Color;
}
"""

FRAG_SHADER = """
#version 130
in vec3 v_normal;
flat in vec4 v_color;
out vec4 fragColor;
void main() {
    // Color only flat tops by vertex color (now flat across each hex)
    if (v_normal.z > 0.99) {
        fragColor = v_color;
    } else {
        fragColor = vec4(1.0, 0.0, 1.0, 1.0);
    }
}
"""
global shader
shader = Shader.make(Shader.SLGLSL, VERT_SHADER, FRAG_SHADER)


def create_flat_top_hexagon_vertices(radius, center=(0, 0, 0)):
    """Generate 6 corner verts + center for flat-topped hexagon."""
    cx, cy, cz = center
    verts = []
    for i in range(6):
        ang = math.radians(60 * i)
        verts.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang), cz))
    verts.append((cx, cy, cz))
    return verts


def get_hex_spacing(radius):
    """Return horizontal and vertical spacing for flat-topped hexes."""
    return 1.5 * radius, math.sqrt(3) * radius


def generate_hex_grid_mesh(radius, tiles: List["BaseTile"] = None, cols=10, rows=10):
    """
    Generate combined vertex list, triangle indices, and an index map for each hex,
    using each tile’s own elevation (pos_z) if provided.

    :param radius: float radius of each hex.
    :param tiles:  Optional list of BaseTile instances (must have .x, .y, and .pos_z).
    :param cols:   Number of columns if not using tiles.
    :param rows:   Number of rows if not using tiles.
    :return: (vertices, triangles, hex_starts)
        - vertices: List of (x, y, z) coords for every vertex.
        - triangles: List of (i1, i2, i3) index triples.
        - hex_starts: List of starting vertex‐indices for each hex cell.
        - hex_centers: List of (x, y, z) coords for each hex center.
        - center_height: Height of the hex center (z coordinate).
    """
    horiz, vert = get_hex_spacing(radius)

    # Build a list of (col, row, height) triples.
    if tiles:
        # Use each BaseTile’s pos_z
        coords = [(t.x, t.y, t.calculate_z_pos_on_altitude()[2]) for t in tiles]
    else:
        # Flat grid at z=0
        coords = [(c, r, 0.0) for c in range(cols) for r in range(rows)]

    verts: List[Tuple[float, float, float]] = []
    tris: List[Tuple[int, int, int]] = []
    hex_starts: List[int] = []
    offset = 0
    hex_centers: List[Tuple[float, float, float]] = []
    center_height = 0.0
    for col, row, height in coords:
        # Mark where this hex’s vertices begin
        hex_starts.append(offset)

        cx = col * horiz
        cy = row * vert + (vert * 0.5 if (col % 2) else 0.0)
        hex_centers.append((cx, cy, height))

        hverts = create_flat_top_hexagon_vertices(radius, (cx, cy, height))
        center_idx = len(hverts) - 1

        # Build the triangle fan around the center
        for i in range(6):
            tris.append((offset + center_idx, offset + i, offset + (i + 1) % 6))

        # Append these verts and advance the offset
        verts.extend(hverts)
        offset += len(hverts)
        center_height = height

    return verts, tris, hex_starts, hex_centers, center_height


def generate_hex_walls(
    center: Tuple[float, float, float],
    radius: float,
    bottom_z: float = 0.0,
    color: Tuple4f = Colors.MAGENTA,
) -> NodePath:
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("hex_walls", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")

    cx, cy, cz = center
    top_verts = [
        (cx + radius * math.cos(math.radians(60 * i)), cy + radius * math.sin(math.radians(60 * i)), cz)
        for i in range(6)
    ]

    # 1) create with one arg, 2) convert to indexed form
    prim = GeomTriangles(Geom.UHStatic)
    prim.make_indexed()

    idx = 0
    for i in range(6):
        a, b = top_verts[i], top_verts[(i + 1) % 6]
        a_bot = (a[0], a[1], bottom_z)
        b_bot = (b[0], b[1], bottom_z)

        # add 4 verts
        for v in (a, b, b_bot, a_bot):
            vw.addData3f(*v)
            nw.addData3f(0, 0, 1)
            cw.addData4f(*color)

        # two triangles per wall quad
        prim.addVertices(idx, idx + 1, idx + 2)
        prim.addVertices(idx, idx + 2, idx + 3)
        idx += 4

    # close once
    prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode("hex_walls")
    node.addGeom(geom)
    wall_np = NodePath(node)
    wall_np.setTwoSided(True)
    wall_np.setLightOff()
    wall_np.setBin("fixed", 0)
    wall_np.setDepthTest(True)
    wall_np.setDepthWrite(True)
    return wall_np


def build_geom_node(
    vertices: List[Tuple[float, float, float]],
    triangles: List[Tuple[int, int, int]],
    hex_starts: List[int] = None,
    tiles: List["BaseTile"] = None,
) -> NodePath:
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("hex_grid", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")

    def default_color(tile):
        c = tile.get_terrain().get_fallback_color()
        if not isinstance(c, (tuple, list)):
            c = tuple(map(float, c))
        return (*c[:3], c[3] if len(c) == 4 else 1.0)

    current = 0
    next_start = hex_starts[1] if hex_starts and len(hex_starts) > 1 else len(vertices)
    for i, (x, y, z) in enumerate(vertices):
        if hex_starts and i >= next_start:
            current += 1
            next_start = hex_starts[current + 1] if current + 1 < len(hex_starts) else len(vertices)
        vw.addData3(x, y, z)
        nw.addData3(0, 0, 1)
        if tiles:
            r, g, b, a = default_color(tiles[current])
        else:
            r, g, b, a = (1, 1, 1, 1)
        cw.addData4(r, g, b, a)

    # create & convert to indexed
    prim = GeomTriangles(Geom.UHStatic)
    prim.make_indexed()
    for a, b, c in triangles:
        prim.addVertices(a, b, c)
    prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode("hex_grid")
    node.addGeom(geom)

    np = NodePath(node)
    global shader
    np.setShader(shader)
    np.setTwoSided(True)
    np.setLightOff()
    return np


def create_hex_grid_node(
    radius: float = 1.0,
    tiles: List["BaseTile"] = None,
    cols: int = None,
    rows: int = None,
) -> NodePath:
    verts, tris, starts, centers, _ = generate_hex_grid_mesh(radius, tiles=tiles, cols=cols or 10, rows=rows or 10)

    grid_np = build_geom_node(verts, tris, hex_starts=starts, tiles=tiles)
    grid_np.setShaderAuto()
    grid_np.setTwoSided(True)
    grid_np.setLightOff()

    # now attach walls only for elevated hexes
    for cx, cy, cz in centers:
        if cz > 0:
            wall_np = generate_hex_walls(center=(cx, cy, cz), radius=radius, bottom_z=0.0)
            wall_np.reparentTo(grid_np)
            wall_np.setBin("fixed", 0)

    return grid_np
