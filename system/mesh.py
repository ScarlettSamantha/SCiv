from typing import Dict, List, Tuple, Optional, TYPE_CHECKING, Any
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
from helpers.tiles import Tiles

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

    def _build_height_map(self) -> dict[Tuple[int, int], float]:
        height_map: dict[Tuple[int, int], float] = {}
        if self.tiles:
            for t in self.tiles:
                height_map[(t.x, t.y)] = t.calculate_z_pos_on_altitude()[2]
        else:
            for c in range(self.cols):
                for r in range(self.rows):
                    height_map[(c, r)] = 0.0
        return height_map

    def build_merged_hex_walls(
        self,
        bottom_z: float = 0.0,
        color: Tuple4f = Colors.MAGENTA,
    ) -> NodePath:
        height_map = self._build_height_map()

        fmt: Any = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("merged_walls", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        cw = GeomVertexWriter(vdata, "color")

        prim = GeomTriangles(Geom.UHStatic)
        prim.make_indexed()

        horiz, vert = self.get_hex_spacing(self.radius)

        # 4) Clear any old records
        self.wall_starts.clear()
        self.wall_vertex_counts.clear()

        idx = 0

        for tile in self.tiles:
            col, row, cz = tile.x, tile.y, tile.calculate_z_pos_on_altitude()[2]
            # If tileZ ≤ bottom_z, no walls at all:
            if cz <= bottom_z:
                self.wall_starts.append(None)
                self.wall_vertex_counts.append(0)
                continue

            start_row = idx

            dirs = Tiles.get_directions_per_col(col)  # Get the correct directions for this column

            wall_pieces: Dict[int, bool] = {0: False, 1: False, 2: False, 3: False, 4: False, 5: False}
            for face_i in range(6):
                dx, dy = dirs[face_i]
                nbr_x, nbr_y = col + dx, row + dy
                z_nbr = height_map.get((nbr_x, nbr_y), bottom_z)

                # Cull if neighbor is at or above this tile’s top
                if cz <= z_nbr:
                    continue

                # Compute the two top‐coordinates of this face (world‐space):
                #   angA = 60·face_i,    angB = 60·(face_i+1)
                angA = math.radians(60 * face_i)
                angB = math.radians(60 * ((face_i + 1) % 6))

                # Our tile’s center in world‐space:
                centerX = col * horiz
                centerY = row * vert + (vert * 0.5 if (col % 2) else 0.0)

                ax = centerX + self.radius * math.cos(angA)
                ay = centerY + self.radius * math.sin(angA)
                bx = centerX + self.radius * math.cos(angB)
                by = centerY + self.radius * math.sin(angB)

                # Top vertices (just above cz to avoid z-fighting)
                topA = (ax, ay, cz + 0.02)
                topB = (bx, by, cz + 0.02)

                # Bottom vertices: clamp to max(z_nbr, bottom_z)
                bottom_clamped = max(z_nbr, bottom_z)
                botA = (ax, ay, bottom_clamped)
                botB = (bx, by, bottom_clamped)

                # Write exactly four vertices: [topA, topB, botB, botA]
                for vx, vy, vz in (topA, topB, botB, botA):
                    vw.addData3f(vx, vy, vz)
                    # A dummy normal is fine if you’re using a flat-color shader:
                    nw.addData3f(0, 0, 1)
                    cw.addData4f(*color)

                # Emit two triangles from these four new rows (idx..idx+3)
                prim.addVertices(idx + 0, idx + 1, idx + 2)
                prim.addVertices(idx + 2, idx + 3, idx + 0)

                idx += 4
                wall_pieces[face_i] = True  # This face has a wall
            tile.visible_sides = wall_pieces

            used = idx - start_row
            if used > 0:
                self.wall_starts.append(start_row)
                self.wall_vertex_counts.append(used)
            else:
                # Fully buried by neighbors with ≥ height
                self.wall_starts.append(None)
                self.wall_vertex_counts.append(0)

        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("all_hex_walls")
        node.addGeom(geom)

        return NodePath(node)

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
            for _, (x, y, zv) in enumerate(hverts):
                # map into atlas cell
                vw.addData3f(x, y, zv)
                nw.addData3f(0, 0, 1)
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
