import math
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from helpers.colors import Colors, Tuple4f
from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexReader,
    GeomVertexWriter,
    NodePath,
    PandaNode,
    Shader,  # type: ignore
)

if TYPE_CHECKING:
    from managers.entity import Tile


class HexGrid:
    def __init__(
        self,
        tiles: List["Tile"],
        radius: float = 1.0,
        cols: int = 10,
        rows: int = 10,
        wall_color: Tuple4f = Colors.MAGENTA,
    ):
        from managers.entity import EntityType

        self.entity_type_ref = EntityType.WORLD.value
        self.entity_key: str = "_world_"
        self.radius: float = radius
        self.tiles: List["Tile"] = tiles
        self._tile_index_map: Dict[Tuple[int, int], int] = {(t.x, t.y): i for i, t in enumerate(self.tiles)}
        self.cols = cols or 10
        self.rows = rows or 10

        self.wall_color = wall_color or Colors.MAGENTA

        # Mesh storage
        self.mesh_vertices: List[Tuple[float, float, float]] = []
        self.mesh_triangles: List[Tuple[int, int, int]] = []
        self.hex_starts: List[int] = []
        self.centers: List[Tuple[float, float, float]] = []
        self.center_height: float = 0.0

        self.wall_starts: List[Optional[int]] = []  # For each tile, row‐index in vdata where its walls begin
        self.wall_vertex_counts: List[int] = []  # How many ‘rows’ (vertices) that tile’s walls occupy

        self._hex_uvs: List[Tuple[float, float]] = []

        self.grid_np: Optional[NodePath] = None
        self.walls_np: Optional[NodePath] = None

        if not hasattr(HexGrid, "shader"):
            self.shader: Shader = Shader.make(  # type: ignore
                Shader.SL_GLSL,  # type: ignore
                vertex="assets/shaders/hex_mesh.vert.glsl",
                fragment="assets/shaders/hex_mesh.frag.glsl",  # type: ignore
            )  # type: ignore

        self.root_np: NodePath[PandaNode] = NodePath(PandaNode("hexgrid_root"))
        self.generate_hex_uvs()
        self.generate_mesh()
        self.build_nodes()

        self.root_np.reparent_to(render)  # type: ignore  # noqa: F821
        self.root_np.flatten_light()

    def dump(self) -> Dict[str, Any]:
        state: Dict[str, Any] = self.__dict__.copy()
        state.pop("root_np", None)
        state.pop("grid_np", None)
        state.pop("walls_np", None)
        state.pop("shader", None)
        state.pop("_tile_index_map", None)
        state["mesh_vertices"] = [
            (round(v[0], 3), round(v[1], 3), round(v[2], 3)) for v in self.mesh_vertices
        ]  # rounding for serialization otherwise floats can be too precise which makes compression really bad especially on really big maps.

        return state

    def load_state(self) -> None:
        self._tile_index_map = {(t.x, t.y): i for i, t in enumerate(self.tiles)}

        self.shader = Shader.make(  # type: ignore
            Shader.SL_GLSL,  # type: ignore
            vertex="assets/shaders/hex_mesh.vert.glsl",
            fragment="assets/shaders/hex_mesh.frag.glsl",  # type: ignore
        )

        self.root_np = NodePath(PandaNode("hexgrid_root"))

        self.generate_hex_uvs()
        self.generate_mesh()
        self.build_nodes()

        try:
            self.root_np.reparent_to(render)  # type: ignore
            self.root_np.flatten_light()
        except NameError:
            pass

    def __getstate__(self) -> Dict[str, Any]:
        return {
            "tiles": self.tiles,
            "radius": self.radius,
            "cols": self.cols,
            "rows": self.rows,
            "wall_color": self.wall_color,
            "entity_key": self.entity_key,
        }

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.tiles = state["tiles"]
        self.radius = state["radius"]
        self.cols = state["cols"]
        self.rows = state["rows"]
        self.wall_color = state["wall_color"]
        self.wall_starts = []
        self.wall_vertex_counts = []
        self.mesh_vertices = []
        self.mesh_triangles = []
        self.hex_starts = []
        self.centers = []
        self.center_height = 0.0
        self._hex_uvs = []
        self.grid_np = None
        self.walls_np = None

        self.root_np = NodePath(PandaNode("hexgrid_root"))

        self._tile_index_map = {(t.x, t.y): i for i, t in enumerate(self.tiles)}

        if not hasattr(HexGrid, "shader"):
            HexGrid.shader = Shader.make(
                Shader.SL_GLSL,
                vertex="assets/shaders/hex_mesh.vert.glsl",
                fragment="assets/shaders/hex_mesh.frag.glsl",
            )

        self.generate_hex_uvs()
        self.generate_mesh()
        self.build_nodes()

        # 6) reparent into the scene (if Panda3D is available)
        try:
            self.root_np.reparent_to(render)  # type: ignore
            self.root_np.flatten_light()
        except NameError:
            # no `render` in this context; skip
            pass

    def reset(self):
        self.tiles.clear()
        self.mesh_vertices.clear()
        self.mesh_triangles.clear()
        self.hex_starts.clear()
        self.centers.clear()
        self.center_height = 0.0
        self.wall_starts.clear()
        self.wall_vertex_counts.clear()

        if hasattr(self, "root_np") and self.root_np:
            self.root_np.removeNode()
            del self.root_np

        self.grid_np = None
        self.walls_np = None

    @staticmethod
    def create_flat_top_hexagon_vertices(
        radius: float, center: Tuple[float, float, float] = (0, 0, 0)
    ) -> List[Tuple[float, float, float]]:
        cx, cy, cz = center
        hexagon_vertices: List[Tuple[float, float, float]] = []
        for i in range(6):
            ang = math.radians(60 * i)
            hexagon_vertices.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang), cz))
        hexagon_vertices.append((cx, cy, cz))
        return hexagon_vertices

    @staticmethod
    def get_hex_spacing(radius: float) -> tuple[float, float]:
        return 1.5 * radius, math.sqrt(3) * radius

    def build_merged_hex_walls(
        self,
        bottom_z: float = 0.0,
        color: Tuple4f = Colors.MAGENTA,
    ) -> NodePath:
        fmt: Any = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("merged_walls", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        nw = GeomVertexWriter(vdata, "normal")
        cw = GeomVertexWriter(vdata, "color")

        prim = GeomTriangles(Geom.UHStatic)
        prim.make_indexed()

        horizontal_spacing, vert = self.get_hex_spacing(self.radius)

        self.wall_starts.clear()
        self.wall_vertex_counts.clear()

        idx = 0
        ANG0 = math.radians(0)

        for tile in self.tiles:
            col, row = tile.x, tile.y
            cz = tile.calculate_z_pos_on_altitude()[2]

            if cz <= bottom_z:
                self.wall_starts.append(None)
                self.wall_vertex_counts.append(0)
                tile.visible_sides = {i: False for i in range(6)}
                continue

            start_row = idx

            centerX: float = col * horizontal_spacing
            centerY: float = row * vert + (vert * 0.5 if (col % 2) else 0.0)

            visible_map: Dict[int, bool] = {i: False for i in range(6)}

            for face_i in range(6):
                angA: float = ANG0 + math.radians(60 * face_i)
                angB: float = ANG0 + math.radians(60 * ((face_i + 1) % 6))

                ax: float = centerX + self.radius * math.cos(angA)
                ay: float = centerY + self.radius * math.sin(angA)
                bx: float = centerX + self.radius * math.cos(angB)
                by: float = centerY + self.radius * math.sin(angB)

                topA: Tuple[float, float, float] = (ax, ay, cz + 0.02)
                topB: Tuple[float, float, float] = (bx, by, cz + 0.02)

                bottom_clamped = bottom_z - 0.05
                botA: Tuple[float, float, float] = (ax, ay, bottom_clamped)
                botB: Tuple[float, float, float] = (bx, by, bottom_clamped)

                for vx, vy, vz in (topA, topB, botB, botA):
                    vw.addData3f(vx, vy, vz)
                    nw.addData3f(0.0, 0.0, 1.0)
                    cw.addData4f(*color)

                prim.addVertices(idx + 0, idx + 1, idx + 2)
                prim.addVertices(idx + 2, idx + 3, idx + 0)

                idx += 4
                visible_map[face_i] = True

            used = idx - start_row
            if used > 0:
                self.wall_starts.append(start_row)
                self.wall_vertex_counts.append(used)
            else:
                self.wall_starts.append(None)
                self.wall_vertex_counts.append(0)

            tile.visible_sides = visible_map

        prim.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("all_hex_walls")
        node.addGeom(geom)

        return NodePath(node)

    def generate_mesh(self):
        horizontal_spacing, vert = self.get_hex_spacing(self.radius)
        if self.tiles:
            coords = [(t.x, t.y, t.calculate_z_pos_on_altitude()[2]) for t in self.tiles]
        else:
            coords = [(c, r, 0.0) for c in range(self.cols) for r in range(self.rows)]

        vertices_list: List[Tuple[float, float, float]] = []
        triangles: List[Tuple[int, int, int]] = []
        hex_starts: List[int] = []
        centers: List[Tuple[float, float, float]] = []
        center_height = 0.0
        offset = 0

        for col, row, height in coords:
            hex_starts.append(offset)
            cx = col * horizontal_spacing
            cy = row * vert + (vert * 0.5 if (col % 2) else 0.0)
            centers.append((cx, cy, height))
            hexagon_vertices = self.create_flat_top_hexagon_vertices(self.radius, (cx, cy, height))
            center_idx = len(hexagon_vertices) - 1
            for i in range(6):
                triangles.append((offset + center_idx, offset + i, offset + (i + 1) % 6))
            vertices_list.extend(hexagon_vertices)
            offset += len(hexagon_vertices)
            center_height = height

        self.mesh_vertices = vertices_list
        self.mesh_triangles = triangles
        self.hex_starts = hex_starts
        self.centers = centers
        self.center_height = center_height

    def get_tile_index_from_coords(self, x: int, y: int) -> int:
        if self.tiles:
            try:
                return self._tile_index_map[(x, y)]
            except KeyError:
                raise ValueError(f"Tile at coordinates ({x}, {y}) not found.")
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
        self.grid_np.reparentTo(self.root_np)  # type: ignore

        self.walls_np = self.build_merged_hex_walls(bottom_z=0.0, color=self.wall_color)
        self.walls_np.setLightOff()
        self.walls_np.setTwoSided(True)
        self.walls_np.reparentTo(self.root_np)  # type: ignore

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
        horizontal_spacing, vert = self.get_hex_spacing(self.radius)
        # choose coords list
        coords: List[Tuple[float, float, float]] = (
            [(t.x, t.y, t.calculate_z_pos_on_altitude()[2]) for t in self.tiles]
            if self.tiles
            else [(c, r, 0.0) for c in range(self.cols) for r in range(self.rows)]
        )

        vert_idx = 0
        for _, (col, row, z) in enumerate(coords):
            # world center
            cx: float = col * horizontal_spacing
            cy: float = row * vert + (vert * 0.5 if (col % 2) else 0.0)
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

    def set_tile_wall_color(self, tile_index: int, color: Tuple4f) -> None:
        if not self.walls_np:
            return

        record = self.get_wall_record(tile_index)
        if record is None:
            return
        start_row, vertex_count = record

        geom_node: GeomNode = self.walls_np.node()  # type: ignore
        if geom_node.getNumGeoms() == 0:  # safety
            return
        geom: Geom = geom_node.modifyGeom(0)  # type: ignore
        vdata = geom.modifyVertexData()  # type: ignore

        if len(color) == 3:  # type: ignore[attr-defined]
            r, g, b = color  # type: ignore[misc]
            rgba = (r, g, b, 1.0)
        else:
            rgba = tuple(color)  # type: ignore[assignment]

        cw = GeomVertexWriter(vdata, "color")
        end_row = start_row + vertex_count
        for row in range(start_row, end_row):
            cw.setRow(row)
            cw.setData4f(*rgba)  # type: ignore[misc]

    def get_tile_index(self, x: int, y: int) -> int:
        if self.tiles:
            for i, t in enumerate(self.tiles):
                if t.x == x and t.y == y:
                    return i
        else:
            return x * self.rows + y
        raise ValueError("Tile not found")

    def get_tile_index_from_base(self, tile: "Tile") -> int:
        x, y = tile.x, tile.y
        return self.get_tile_index(x, y)
