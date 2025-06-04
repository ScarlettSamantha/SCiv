from typing import List, Tuple, Optional, TYPE_CHECKING, Any
from panda3d.core import (
    Geom,
    GeomNode,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexReader,
    GeomVertexWriter,
    GeomTriangles,
    NodePath,
    PandaNode,
    Shader,  # type: ignore
)
import math

from helpers.colors import Colors, Tuple4f

if TYPE_CHECKING:
    from managers.entity import BaseTile


class HexGrid:
    def __init__(
        self,
        tiles: List["BaseTile"],
        radius: float = 1.0,
        cols: int = 10,
        rows: int = 10,
        wall_color: Tuple4f = Colors.MAGENTA,
    ):
        self.radius: float = radius
        self.tiles: List["BaseTile"] = tiles
        self.cols = cols or 10
        self.rows = rows or 10

        self.wall_color = wall_color or Colors.MAGENTA

        # Mesh storage
        self.verts: List[Tuple[float, float, float]] = []
        self.tris: List[Tuple[int, int, int]] = []
        self.hex_starts: List[int] = []
        self.centers: List[Tuple[float, float, float]] = []
        self.center_height: float = 0.0
        self._hex_uvs: List[Tuple[float, float]] = []

        # Panda3D NodePaths
        self.grid_np: Optional[NodePath] = None
        self.walls_np: Optional[NodePath] = None

        # Create shader only once (class/static)
        if not hasattr(HexGrid, "shader"):
            self.shader: Shader = Shader.make(  # type: ignore
                Shader.SL_GLSL,  # type: ignore
                vertex="assets/shaders/hex_mesh.vert.glsl",
                fragment="assets/shaders/hex_mesh.frag.glsl",  # type: ignore
            )  # type: ignore

        # Initialize mesh data and build nodes
        self.generate_hex_uvs()
        self.generate_mesh()
        self.build_nodes()

        if self.grid_np:
            self.grid_np.flattenStrong()

    @staticmethod
    def create_flat_top_hexagon_vertices(
        radius: float, center: Tuple[float, float, float] = (0, 0, 0)
    ) -> List[Tuple[float, float, float]]:
        cx, cy, cz = center
        verts: List[Tuple[float, float, float]] = []
        for i in range(6):
            ang = math.radians(60 * i)
            verts.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang), cz))
        verts.append((cx, cy, cz))
        return verts

    @staticmethod
    def get_hex_spacing(radius: float) -> tuple[float, float]:
        return 1.5 * radius, math.sqrt(3) * radius

    def generate_mesh(self):
        horiz, vert = self.get_hex_spacing(self.radius)
        if self.tiles:
            coords = [(t.x, t.y, t.calculate_z_pos_on_altitude()[2]) for t in self.tiles]
        else:
            coords = [(c, r, 0.0) for c in range(self.cols) for r in range(self.rows)]

        verts: List[Tuple[float, float, float]] = []
        tris: List[Tuple[int, int, int]] = []
        hex_starts: List[int] = []
        centers: List[Tuple[float, float, float]] = []
        center_height = 0.0
        offset = 0

        for col, row, height in coords:
            hex_starts.append(offset)
            cx = col * horiz
            cy = row * vert + (vert * 0.5 if (col % 2) else 0.0)
            centers.append((cx, cy, height))
            hverts = self.create_flat_top_hexagon_vertices(self.radius, (cx, cy, height))
            center_idx = len(hverts) - 1
            for i in range(6):
                tris.append((offset + center_idx, offset + i, offset + (i + 1) % 6))
            verts.extend(hverts)
            offset += len(hverts)
            center_height = height

        self.verts = verts
        self.tris = tris
        self.hex_starts = hex_starts
        self.centers = centers
        self.center_height = center_height

    def build_merged_hex_walls(self, bottom_z: float = 0.0, color: Tuple4f = Colors.MAGENTA):
        fmt: Any = GeomVertexFormat.getV3n3c4()  # type: ignore
        vdata: GeomVertexData = GeomVertexData("merged_walls", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        cw = GeomVertexWriter(vdata, "color")
        prim: GeomTriangles = GeomTriangles(Geom.UHStatic)
        prim.make_indexed()  # type: ignore

        idx = 0
        for cx, cy, cz in self.centers:
            if cz <= 0.0:
                continue
            top_verts = [
                (
                    cx + self.radius * math.cos(math.radians(60 * i)),
                    cy + self.radius * math.sin(math.radians(60 * i)),
                    cz + 0.02,
                )
                for i in range(6)
            ]
            for i in range(6):
                a, b = top_verts[i], top_verts[(i + 1) % 6]  # type: ignore
                a_bot = (a[0], a[1], bottom_z)  # type: ignore
                b_bot = (b[0], b[1], bottom_z)  # type: ignore
                for v in (a, b, b_bot, a_bot):
                    vw.addData3f(*v)
                    nw.addData3f(1, 1, 1)
                    cw.addData4f(*color)
                prim.addVertices(idx, idx + 1, idx + 2)
                prim.addVertices(idx, idx + 2, idx + 3)
                idx += 4

        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("all_hex_walls")
        node.addGeom(geom)
        return NodePath(node)

    def build_nodes(self):
        # build mesh
        self.grid_np = self.build_geom_node()

        # build walls as before
        self.walls_np = self.build_merged_hex_walls(bottom_z=0.0, color=Colors.MAGENTA)
        self.walls_np.setLightOff()
        self.walls_np.setTwoSided(True)
        self.walls_np.reparentTo(self.grid_np)

    def generate_hex_uvs(self):
        self._hex_uvs = []
        # flat-top orientation: start at -30°, step 60°
        for i in range(6):
            ang = math.radians(60 * i - 30)
            u = (math.cos(ang) + 1.0) * 0.5
            v = math.sin(ang) / math.sqrt(3) + 0.5
            self._hex_uvs.append((u, v))
        # true UV-center of the cell
        self._hex_uvs.append((0.5, 0.5))

    def build_geom_node(self) -> NodePath:
        fmt: Any = GeomVertexFormat.getV3n3c4t2()  # type: ignore
        vdata = GeomVertexData("hex_grid", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        cw = GeomVertexWriter(vdata, "color")
        prim: GeomTriangles = GeomTriangles(Geom.UHStatic)
        prim.make_indexed()  # type: ignore

        # helper for flat-top spacing
        horiz, vert = self.get_hex_spacing(self.radius)
        # choose coords list
        coords: List[Tuple[float, float, float]] = (
            [(t.x, t.y, t.calculate_z_pos_on_altitude()[2]) for t in self.tiles]
            if self.tiles
            else [(c, r, 0.0) for c in range(self.cols) for r in range(self.rows)]
        )

        vert_idx = 0
        for _, (col, row, z) in enumerate(coords):
            # world center
            cx: float = col * horiz
            cy: float = row * vert + (vert * 0.5 if (col % 2) else 0.0)

            # atlas cell

            # build the 7 verts: 6 corners + center
            hverts: List[Tuple[float, float, float]] = self.create_flat_top_hexagon_vertices(self.radius, (cx, cy, z))
            # emit them
            for i, (x, y, zv) in enumerate(hverts):
                # flat-top angl

                # map into atlas cell

                vw.addData3f(x, y, zv)
                nw.addData3f(0, 0, 1)
                cw.addData4f(*self.wall_color)

            # add the 6 triangles (fan around center, which is vert_idx+6)
            center_idx = vert_idx + 6
            for i in range(6):
                prim.addVertices(center_idx, vert_idx + i, vert_idx + (i + 1) % 6)

            vert_idx += 7

        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("hex_grid")
        node.addGeom(geom)

        np = NodePath(node)
        np.flatten_medium()  # type: ignore
        np.setShader(self.shader)  # type: ignore
        np.setTwoSided(True)
        np.setLightOff()

        return np

    def set_tile_color(self, tile_index: int, color: Tuple[float, float, float, float]):
        geom_node: GeomNode = self.grid_np.node()  # type: ignore
        geom: Geom = geom_node.modifyGeom(0)  # type: ignore
        vdata = geom.modifyVertexData()  # type: ignore
        cw = GeomVertexWriter(vdata, "color")
        start = self.hex_starts[tile_index]
        count = 7
        for vi in range(start, start + count):
            cw.setRow(vi)
            cw.setData4f(*color + (1.0,))  # type: ignore
        # (Optional) read back for debugging
        reader = GeomVertexReader(vdata, "color")
        reader.setRow(start)
        print(f"Vertex {start} new color:", reader.getData4f())

    def set_tile_wall_color(self, tile_index: int, color: Tuple[float, float, float, float]):
        pandaNode: PandaNode = self.walls_np.node()  # type: ignore
        geom_node: GeomNode = pandaNode.find("**/all_hex_walls").node()  # type: ignore

        if not geom_node:
            raise ValueError("No walls node found in HexGrid.")

        geom: Geom = geom_node.modifyGeom(0)  # type: ignore
        vdata = geom.modifyVertexData()  # type: ignore
        cw = GeomVertexWriter(vdata, "color")  # type: ignore
        start = tile_index * 12
        count = 12
        for vi in range(start, start + count):
            cw.setRow(vi)
            cw.setData4f(*color + (1.0,))  # type: ignore

    def get_tile_index(self, x: int, y: int) -> int:
        if self.tiles:
            for i, t in enumerate(self.tiles):
                if t.x == x and t.y == y:
                    return i
        else:
            return x * self.rows + y
        raise ValueError("Tile not found")

    def get_tile_index_from_base(self, tile: "BaseTile") -> int:
        x, y = tile.x, tile.y
        return self.get_tile_index(x, y)
