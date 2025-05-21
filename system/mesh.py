from typing import TYPE_CHECKING, List, Tuple
from panda3d.core import (
    Geom,
    GeomNode,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    GeomTriangles,
    LineSegs,
    NodePath,
    Shader,
)
import math

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

    return verts, tris, hex_starts, hex_centers


def generate_hex_walls(
    center: Tuple[float, float, float],
    radius: float,
    height: float = 0.0,
    color=(0.5, 0.5, 0.5, 1.0),
) -> NodePath:
    """
    Creates 6 walls for a flat-topped hexagon, each wall connecting the top edge of the hex to z=0,
    and adds border lines for each wall (2 vertical + 1 bottom).
    """
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("hex_walls", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")

    cx, cy, cz = center
    verts = []

    # Generate 6 top corners around the hex
    for i in range(6):
        angle = math.radians(60 * i)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        z = cz
        verts.append((x, y, z))

    prim = GeomTriangles(Geom.UHStatic)
    index = 0

    # For wall border lines
    ls = LineSegs()
    ls.setColor(0, 0, 0, 1)
    ls.setThickness(1.0)

    for i in range(6):
        a = verts[i]
        b = verts[(i + 1) % 6]
        a_bottom = (a[0], a[1], height)
        b_bottom = (b[0], b[1], height)

        # Add the 4 vertices of the quad (a, b, b_bottom, a_bottom)
        for v in [a, b, b_bottom, a_bottom]:
            vw.addData3f(*v)
            nw.addData3f(0, 0, 1)
            cw.addData4f(*color)

        # Add triangles for the wall quad
        prim.addVertices(index, index + 1, index + 2)
        prim.addVertices(index, index + 2, index + 3)
        prim.closePrimitive()
        index += 4

        # Add vertical and bottom lines
        ls.moveTo(*a)
        ls.drawTo(*a_bottom)

        ls.moveTo(*b)
        ls.drawTo(*b_bottom)

        ls.moveTo(*a_bottom)
        ls.drawTo(*b_bottom)

    # Build wall geometry
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    wall_node = GeomNode("hex_walls")
    wall_node.addGeom(geom)
    wall_np = NodePath(wall_node)
    wall_np.setTwoSided(True)
    wall_np.setLightOff()
    wall_np.setBin("fixed", 0)  # render after the tile top
    wall_np.setDepthTest(True)
    wall_np.setDepthWrite(True)

    # Build border line geometry
    border_node = ls.create()
    border_np = NodePath(border_node)
    border_np.reparentTo(wall_np)
    border_np.setBin("fixed", 20)  # render above walls but still respect depth
    border_np.setDepthTest(True)
    border_np.setDepthWrite(True)

    return wall_np


def build_geom_node(
    vertices,
    triangles,
    hex_starts=None,
    tiles=None,
):
    """
    Build and return a NodePath from mesh data with per‐hex coloring.

    :param vertices: List of (x,y,z) coords.
    :param triangles: List of (i1, i2, i3) tuples.
    :param hex_starts: List of start indices into vertices for each hex.
    :param tiles:      Parallel list of BaseTile instances (one per hex).
    :param hex_color_func: Function(tile: BaseTile) -> (r,g,b,a).
    """
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("hexgrid", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")

    # fallback white
    def default_color(tile: "BaseTile"):
        color = tile.get_terrain().get_fallback_color()
        # If color is not a tuple/list, try to convert it (e.g., from LRGBColor)
        if not isinstance(color, (tuple, list)):
            color = tuple(float(c) for c in color)
        # Ensure color is a tuple of 4 floats (RGBA)
        if len(color) == 3:
            return (float(color[0]), float(color[1]), float(color[2]), 1.0)
        elif len(color) == 4:
            return (float(color[0]), float(color[1]), float(color[2]), float(color[3]))
        else:
            # fallback to white
            return (1.0, 1.0, 1.0, 1.0)

    current_hex = 0
    # pre‐compute where each hex’s vertices end
    next_start = hex_starts[1] if hex_starts and len(hex_starts) > 1 else len(vertices)

    for idx, (x, y, z) in enumerate(vertices):
        # bump hex index when we pass its start
        if hex_starts and idx >= next_start:
            current_hex += 1
            next_start = hex_starts[current_hex + 1] if current_hex + 1 < len(hex_starts) else len(vertices)

        vw.addData3(x, y, z)
        nw.addData3(0, 0, 1)

        # pass the actual BaseTile into your color fn
        tile = tiles[current_hex] if tiles is not None else None
        r, g, b, a = default_color(tile)
        cw.addData4(r, g, b, a)

    prim = GeomTriangles(Geom.UHStatic)
    for a, b, c in triangles:
        prim.addVertices(a, b, c)
        prim.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(prim)
    node = GeomNode("hex_grid")
    node.addGeom(geom)
    np = NodePath(node)

    # apply the flat‐color shader you already wrote
    shader = Shader.make(Shader.SLGLSL, VERT_SHADER, FRAG_SHADER)
    np.setShader(shader)
    np.setTwoSided(True)
    np.setLightOff()
    return np


def create_hex_grid_node(
    radius=1,
    tiles=None,
    cols=None,
    rows=None,
    hex_color_func=None,
    show_borders=True,  # new flag
):
    """
    High‐level: build a colored hex grid from either:
      - tiles: list of BaseTile (must have x,y attrs)
      - cols & rows: explicit grid size
    :param show_borders: if True, draws thin black outlines around each hex top.
    """
    verts, tris, starts, centers = generate_hex_grid_mesh(
        radius,
        tiles=tiles,
        cols=cols or 10,
        rows=rows or 10,
    )
    # build the filled, shaded mesh
    grid_np = build_geom_node(
        verts,
        tris,
        hex_starts=starts,
        tiles=tiles,
    )

    for center in centers:
        wall_np = generate_hex_walls(center=center, radius=radius, height=0.0)
        wall_np.reparentTo(grid_np)
        wall_np.setBin("fixed", 0)  # render after the tile top

    if show_borders:
        ls = LineSegs()
        ls.setColor(0, 0, 0, 1)  # black borders
        ls.setThickness(3.0)
        # for each hex, draw a closed loop around its 6 corners
        for start in starts:
            # grab the 6 corner positions (the 7th vert is the center)
            corners = [verts[start + i] for i in range(6)]
            ls.moveTo(corners[-1])
            for p in corners:
                ls.drawTo(p)

        border_node = ls.create()
        border_np = NodePath(border_node)
        border_np.reparentTo(grid_np)
        # ensure borders aren’t depth-tested away
        border_np.setDepthTest(True)
        border_np.setDepthWrite(True)
        border_np.setBin("fixed", 0)

    return grid_np
