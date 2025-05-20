import math
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    GeomTriangles,
    Geom,
    GeomNode,
    NodePath,
    Shader,
)

# Offsets for odd-q flat-topped hex grid
EVEN_Q_NEIGHBORS = [(1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
ODD_Q_NEIGHBORS = [(1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1), (1, 0)]


class HexMeshGenerator:
    """
    Generates a mesh for a single hex tile with 90° vertical walls,
    optionally clamped to ground (z=0) to avoid overly long walls.
    """

    def __init__(self, radius=0.5, height_scale=1.0, clamp_to_ground=True):
        self.radius = radius
        self.height_scale = height_scale
        self.clamp_to_ground = clamp_to_ground
        self.format = GeomVertexFormat.get_v3n3()

    def _neighbor_offsets(self, q: int):
        return ODD_Q_NEIGHBORS if (q & 1) else EVEN_Q_NEIGHBORS

    def _add_wall(self, i, ring, h0, h1, vwriter, nwriter, tris, next_index):
        """
        Draws a vertical wall between heights h0 and h1 at edge i.
        If clamp_to_ground is True, the lower height goes to 0 instead of h1.
        Returns updated next_index.
        """
        z_top = max(h0, h1)
        z_bot = 0.0 if self.clamp_to_ground else min(h0, h1)
        t1, t2 = i + 1, ((i + 1) % 6) + 1
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % 6]
        # bottom verts
        vwriter.addData3(x1, y1, z_bot)
        nwriter.addData3(0, 0, 0)
        vwriter.addData3(x2, y2, z_bot)
        nwriter.addData3(0, 0, 0)
        b1, b2 = next_index, next_index + 1
        next_index += 2
        # calc normal
        ex, ey = x2 - x1, y2 - y1
        nx, ny = ey, -ex
        length = math.hypot(nx, ny)
        if length:
            nx /= length
            ny /= length
        # set normals for quad vertices
        for vid in (t1, t2, b2, b1):
            nwriter.setRow(vid)
            nwriter.setData3(nx, ny, 0)
        # two triangles
        tris.addVertices(t1, t2, b2)
        tris.addVertices(t1, b2, b1)
        return next_index

    def build_tile(self, q: int, r: int, height_map: dict) -> NodePath:
        """
        Builds the mesh for a tile at (q,r), with walls to neighbors.
        """
        h0 = height_map.get((q, r), 0.0) * self.height_scale
        offsets = self._neighbor_offsets(q)
        # ring coords
        ring = [
            (self.radius * math.cos(math.radians(60 * i + 30)), self.radius * math.sin(math.radians(60 * i + 30)))
            for i in range(6)
        ]
        # setup vertex data
        vdata = GeomVertexData(f"hex_{q}_{r}", self.format, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        # top center
        vw.addData3(0, 0, h0)
        nw.addData3(0, 0, 1)
        # top ring
        for x, y in ring:
            vw.addData3(x, y, h0)
            nw.addData3(0, 0, 1)
        tris = GeomTriangles(Geom.UHStatic)
        for i in range(6):
            tris.addVertices(0, i + 1, (i + 1) % 6 + 1)
        next_index = 7
        # walls
        for i, (dq, dr) in enumerate(offsets):
            h1 = height_map.get((q + dq, r + dr), 0.0) * self.height_scale
            if h1 != h0:
                next_index = self._add_wall(i, ring, h0, h1, vw, nw, tris, next_index)
        # assemble
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode(f"hexnode_{q}_{r}")
        node.addGeom(geom)
        np = NodePath(node)
        np.setTwoSided(True)
        shader = Shader.load(Shader.SL_GLSL, "assets/shaders/hex.vert.glsl", "assets/shaders/hex.frag.glsl")
        np.setShader(shader)
        return np
