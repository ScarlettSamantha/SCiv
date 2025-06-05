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

        self.wall_starts: List[Optional[int]] = []  # For each tile, row‐index in vdata where its walls begin
        self.wall_vertex_counts: List[int] = []  # How many ‘rows’ (vertices) that tile’s walls occupy

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

    def build_merged_hex_walls(self, bottom_z: float = 0.0, color: Tuple4f = Colors.MAGENTA) -> NodePath:
        """
        Build one big GeomNode containing all the “towers” (walls) of each hex
        whose center‐height > 0. As we go, record for each tile:
          - wall_starts[i]: the first row index in the merged vdata
          - wall_vertex_counts[i]: how many rows (vertices) that tile occupies

        If a tile has cz <= 0.0, we record None and 0.
        """
        fmt: Any = GeomVertexFormat.getV3n3c4()  # v3, normal, color4
        vdata: GeomVertexData = GeomVertexData("merged_walls", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        cw = GeomVertexWriter(vdata, "color")
        prim: GeomTriangles = GeomTriangles(Geom.UHStatic)
        prim.make_indexed()  # for indexed prim

        # Clear out any old records, then rebuild.
        self.wall_starts.clear()
        self.wall_vertex_counts.clear()

        idx = 0  # running “row” counter
        for _, (cx, cy, cz) in enumerate(self.centers):
            if cz <= 0.0:
                # no wall for this tile: record as None
                self.wall_starts.append(None)
                self.wall_vertex_counts.append(0)
                continue

            # mark the start of this tile’s wall geometry
            start_row = idx
            # each hex‐tower has 6 faces; each face we emit 4 vertices.
            # total rows = 6 * 4 = 24
            # (We’ll still do the loop as before so normals/colors get written.)
            top_verts = [
                (
                    cx + self.radius * math.cos(math.radians(60 * i)),
                    cy + self.radius * math.sin(math.radians(60 * i)),
                    cz + 0.02,
                )
                for i in range(6)
            ]

            for i in range(6):
                a, b = top_verts[i], top_verts[(i + 1) % 6]
                a_bot = (a[0], a[1], bottom_z)
                b_bot = (b[0], b[1], bottom_z)
                for v in (a, b, b_bot, a_bot):
                    vw.addData3f(*v)
                    nw.addData3f(1, 1, 1)
                    cw.addData4f(*color)
                # two triangles per face, referencing those 4 new rows:
                prim.addVertices(idx, idx + 1, idx + 2)
                prim.addVertices(idx + 2, idx + 3, idx + 0)
                idx += 4

            # done writing all six faces: record that this tile’s walls occupy 24 rows:
            self.wall_starts.append(start_row)
            self.wall_vertex_counts.append(6 * 4)

        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("all_hex_walls")
        node.addGeom(geom)
        return NodePath(node)

    def get_tile_index_from_coords(self, x: int, y: int) -> int:
        """
        Get the tile index from the given coordinates (x, y).
        If tiles are defined, it searches through them; otherwise, it calculates based on rows and cols.
        """
        if self.tiles:
            for i, t in enumerate(self.tiles):
                if t.x == x and t.y == y:
                    return i
        else:
            if 0 <= x < self.cols and 0 <= y < self.rows:
                return x * self.rows + y
        raise ValueError(f"Tile at coordinates ({x}, {y}) not found.")

    def get_wall_record(self, tile_index: int) -> Optional[Tuple[int, int]]:
        """
        Return (start_row, vertex_count) for that tile’s wall in the merged Geom.
        If that tile had no wall (height <= 0), returns None.
        """
        if tile_index < 0 or tile_index >= len(self.centers):
            raise IndexError(f"tile_index {tile_index} out of range")

        start = self.wall_starts[tile_index]
        count = self.wall_vertex_counts[tile_index]
        if start is None or count == 0:
            return None
        return (start, count)

    def set_wall_color_for_tile(self, tile_index: int, new_color: Tuple4f) -> None:
        """
        Overwrite the vertex‐colors for the wall of a single hex (by tile_index).
        If that tile has no wall (height ≤ 0), this does nothing.
        """
        # Make sure walls exist
        if not self.walls_np:
            return

        # Look up the record we stored during build_merged_hex_walls()
        record = self.get_wall_record(tile_index)
        if record is None:
            return  # this tile had no wall

        start_row, vertex_count = record

        # Grab the GeomVertexData from the existing merged node
        geom_node: GeomNode = self.walls_np.node()  # type: ignore
        geom = geom_node.modifyGeom(0)  # type: ignore
        vdata = geom.modifyVertexData()  # type: ignore

        # Prepare a writer on the "color" column (c4f)
        cw = GeomVertexWriter(vdata, "color")

        # Overwrite only the rows [start_row .. start_row + vertex_count)
        for row in range(start_row, start_row + vertex_count):
            cw.setRow(row)
            cw.setData4f(*new_color)

    def get_all_wall_records(self) -> List[Tuple[int, int, int]]:
        """
        Return a list of (tile_index, start_row, vertex_count) for every tile that actually has walls.
        """
        records: List[Tuple[int, int, int]] = []
        for i, start in enumerate(self.wall_starts):
            if start is not None and self.wall_vertex_counts[i] > 0:
                records.append((i, start, self.wall_vertex_counts[i]))
        return records

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
