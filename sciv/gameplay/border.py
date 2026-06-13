import io
import math
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Set, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from gameplay.repositories.tile import TileRepository
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.geometry import generate_flat_top_hex
from helpers.os import WindowsHelper
from helpers.tiles import Tiles
from managers.player import PlayerManager
from mixins.singleton import Singleton
from panda3d.core import (
    AntialiasAttrib,
    ClockObject,
    LVecBase3f,
    LineSegs,
    NodePath,
    PNMImage,
    Shader,  # type: ignore
    StringStream,  # type: ignore
    Texture,  # type: ignore
    TransparencyAttrib,  # type: ignore
)
from PIL import Image
from system.shaders import Shaders

if TYPE_CHECKING:
    from gameplay.player import Player


BorderEdgeFlags = Tuple[float, float, float, float, float, float]


class Borders(DirectObject, Singleton):
    HEX_DIRECTIONS = Tiles.get_directions_dirs()

    COLOR_HEX_TOP_BORDERS = Colors.MAGENTA
    COLOR_HEX_WALLS = Colors.BLACK

    TOP_BORDER_SCALE = 1.0
    TOP_BORDER_EMPIRE_SCALE = 0.98

    BORDER_RADIUS = 0.985
    BORDER_Z_OFFSET = 0.052
    BORDER_SHADOW_Z_OFFSET = 0.047
    BORDER_HIGHLIGHT_Z_OFFSET = 0.058

    BORDER_MAIN_THICKNESS = 2.4
    BORDER_SHADOW_THICKNESS = 5.8
    BORDER_HIGHLIGHT_THICKNESS = 1.1

    BORDER_DASH_LENGTH = 0.24
    BORDER_DASH_VISIBLE_LENGTH = 0.18

    BORDER_MAIN_ALPHA = 0.62
    BORDER_SHADOW_ALPHA = 0.24
    BORDER_HIGHLIGHT_ALPHA = 0.24

    BORDER_PLAYER_COLOR_WEIGHT = 0.68
    BORDER_WORLD_BLEND_COLOR = (0.72, 0.68, 0.52)

    def __init__(
        self,
        map_size: Tuple[int, int],
        shader_system: Shaders,
        parent: NodePath,
    ):
        self.map_width, self.map_height = map_size
        self.shader_system = shader_system
        self.parent = parent
        self.base = Cache.get_showbase_instance()

        self.border_nodes: Dict[str, List[NodePath]] = {}
        self.border_textures: Dict[str, Texture] = {}

        self.logger = Cache.get_showbase_instance().logger.get_singleton_instance().graphics.getChild("borders")

        path_border_vert = str(self.base.base_path / "assets/shaders/border.vert")
        path_border_frag = str(self.base.base_path / "assets/shaders/border_ring.frag")

        path_hex_border_vert = str(self.base.base_path / "assets/shaders/hex_border.vert")
        path_hex_border_frag = str(self.base.base_path / "assets/shaders/hex_border.frag")

        if WindowsHelper.is_windows():
            path_border_vert = WindowsHelper.win32_to_unix_path(path_border_vert)
            path_border_frag = WindowsHelper.win32_to_unix_path(path_border_frag)
            path_hex_border_vert = WindowsHelper.win32_to_unix_path(path_hex_border_vert)
            path_hex_border_frag = WindowsHelper.win32_to_unix_path(path_hex_border_frag)

        self.shader = self.shader_system.load_shader(
            "borders",
            path_border_vert,
            path_border_frag,
        )
        self.hex_border_shader: Shader = self.shader_system.load_shader(
            "hex_borders",
            path_hex_border_vert,
            path_hex_border_frag,
        )

        self.base.taskMgr.setupTaskChain("borders", numThreads=1)
        self.accept("borders.task_done", self._on_task_done)

        self.setup_borders()
        self.register()

    def register(self) -> None:
        Cache.get_showbase_instance().taskMgr.add(self.update_border_times, "update_border_shader_times", delay=5)
        self.accept("game.border.refresh", self.refresh)

    def setup_borders(self) -> None:
        self.reset()

        for tex in self.border_textures.values():
            tex.release_all()
        self.border_textures.clear()

        for p in PlayerManager.all().values():
            self._enqueue_player(p)

    def refresh(self, *args: Any) -> None:
        self.reset()
        self.border_textures.clear()

        for p in PlayerManager.all().values():
            self._enqueue_player(p)

        MessengerGlobal.messenger.send("ui.borders.updated")

    def reset(self) -> None:
        for nodes in self.border_nodes.values():
            for node in nodes:
                node.remove_node()

        self.border_nodes.clear()

    def _enqueue_player(self, player: "Player") -> None:
        player_id = player.id
        if player_id is None:
            self.logger.error("[Borders] Cannot enqueue border generation for player without an id")
            return

        owned = set(player.get_all_tiles())
        growing = set(player.get_all_tiles_marked_for_border_growth())
        task_name = f"generate_border_mask_{player_id}"

        Cache.get_showbase_instance().taskMgr.add(
            self._async_mask_task,
            task_name,
            extraArgs=[player_id, owned, growing],
            appendTask=False,
            taskChain="borders",
        )

    def _async_mask_task(
        self,
        player_id: str,
        owned: Set[Tuple[int, int]],
        growing: Set[Tuple[int, int]],
    ) -> bool:
        mask = PNMImage(self.map_width, self.map_height, 3)
        mask.fill(0)

        for x, y in owned:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_red(x, y, 1.0)

        for x, y in growing:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_green(x, y, 1.0)

        mask.flip(False, True, False)

        MessengerGlobal.messenger.send("borders.task_done", [player_id, mask])
        return Task.done  # type: ignore

    def _on_task_done(self, player_id: str, mask: PNMImage) -> None:
        tex = Texture(f"border_mask_{player_id}")
        tex.load(mask)
        tex.set_magfilter(Texture.FT_nearest)
        tex.set_minfilter(Texture.FT_nearest)
        self.border_textures[player_id] = tex

        for node in self.border_nodes.get(player_id, []):
            node.remove_node()

        player = PlayerManager.all()[int(player_id)]
        self.border_nodes[player_id] = self._create_empire_border_hexes(player)

        MessengerGlobal.messenger.send("ui.borders.updated")

    def generate_world_border_mask(
        self,
        map_size: Tuple[int, int] = (25, 25),
        hex_radius_px: int = 50,
        bg_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> Texture:
        cols, rows = map_size
        player_tiles: Set[Tuple[int, int]] = set()

        for player in PlayerManager.all().values():
            tiles_p = set(player.get_all_tiles().keys()) | set(player.get_all_tiles_marked_for_border_growth().keys())
            player_tiles.update(tiles_p)

        self.player_tiles = player_tiles

        r = hex_radius_px
        w = 2 * r
        h = int(math.sqrt(3) * r)
        horizontal = int(1.5 * r)
        vert = h
        img_w = horizontal * (cols - 1) + w
        img_h = vert * rows + r

        img = Image.new("RGB", (img_w, img_h), bg_color)

        pnm = PNMImage()
        with io.BytesIO() as buf:
            img.save(buf, format="PNG")
            buf.seek(0)
            stream = StringStream(buf.getvalue())
            pnm.read(stream)

        tex = Texture()
        tex.load(pnm)
        tex.set_magfilter(Texture.FT_nearest)
        tex.set_minfilter(Texture.FT_nearest)

        return tex

    def generate_world_border_nodes(self) -> List[NodePath]:
        from managers.world import World

        self.world_hexes: List[NodePath] = []
        grid = World.get_singleton_instance().get_grid()
        hex_model = generate_flat_top_hex()

        for x, y in grid:
            np = hex_model.copy_to(self.parent)
            np.set_scale(self.TOP_BORDER_SCALE)

            wx, wy, wz = TileRepository.hex_to_world(x, y)
            np.set_pos(LVecBase3f(wx, wy, wz + 0.015))
            np.set_hpr(30, 0, 0)

            self.world_hexes.append(np)

        return self.world_hexes

    def apply_shader_to_hex(self, hex_node: NodePath, color: Tuple4f = COLOR_HEX_TOP_BORDERS) -> None:
        hex_node.set_shader(self.hex_border_shader)
        hex_node.set_shader_input("borderMask", self.hex_border_tex)  # type: ignore
        hex_node.set_shader_input("borderColor", *color)  # type: ignore
        hex_node.set_shader_input("tilePos", (0, 0))  # type: ignore
        hex_node.set_shader_input("mapSize", (self.map_width, self.map_height))  # type: ignore
        hex_node.set_shader_input("edgeMask", 63)  # type: ignore

    def apply_shader_to_hexes(self, hex_nodes: List[NodePath]) -> None:
        for n in hex_nodes:
            self.apply_shader_to_hex(n, self.COLOR_HEX_WALLS)

    def _create_empire_border_hexes(self, player: "Player") -> List[NodePath]:
        owned: Set[Tuple[int, int]] = set(player.get_all_tiles())
        growing: Set[Tuple[int, int]] = set(player.get_all_tiles_marked_for_border_growth())
        territory: Set[Tuple[int, int]] = owned | growing

        if not territory:
            return []

        main_color = self._soft_player_color(player.color, self.BORDER_MAIN_ALPHA)
        shadow_color = (0.04, 0.035, 0.025, self.BORDER_SHADOW_ALPHA)
        highlight_color = self._lighten_color(main_color, self.BORDER_HIGHLIGHT_ALPHA)

        nodes: List[NodePath] = []

        shadow_node = self._create_border_line_node(
            name=f"empire_border_shadow_{player.id}",
            territory=territory,
            color=shadow_color,
            thickness=self.BORDER_SHADOW_THICKNESS,
            z_offset=self.BORDER_SHADOW_Z_OFFSET,
            bin_order=38,
        )
        if shadow_node is not None:
            nodes.append(shadow_node)

        main_node = self._create_border_line_node(
            name=f"empire_border_main_{player.id}",
            territory=territory,
            color=main_color,
            thickness=self.BORDER_MAIN_THICKNESS,
            z_offset=self.BORDER_Z_OFFSET,
            bin_order=40,
        )
        if main_node is not None:
            nodes.append(main_node)

        highlight_node = self._create_border_line_node(
            name=f"empire_border_highlight_{player.id}",
            territory=territory,
            color=highlight_color,
            thickness=self.BORDER_HIGHLIGHT_THICKNESS,
            z_offset=self.BORDER_HIGHLIGHT_Z_OFFSET,
            bin_order=41,
        )
        if highlight_node is not None:
            nodes.append(highlight_node)

        return nodes

    def _create_border_line_node(
        self,
        name: str,
        territory: Set[Tuple[int, int]],
        color: Tuple4f,
        thickness: float,
        z_offset: float,
        bin_order: int,
    ) -> NodePath | None:
        segs = LineSegs(name)
        segs.set_thickness(thickness)
        segs.set_color(*color)

        has_segments = False

        for x, y in territory:
            for edge_start, edge_end in self._iter_exposed_border_edges(x, y, territory, z_offset):
                has_segments = True
                self._append_dashed_edge(segs, edge_start, edge_end)

        if not has_segments:
            return None

        node = NodePath(segs.create())
        node.reparent_to(self.parent)
        node.set_transparency(TransparencyAttrib.M_alpha)
        node.set_bin("fixed", bin_order)
        node.set_depth_write(False)
        node.set_depth_test(True)
        node.set_antialias(AntialiasAttrib.MLine)

        return node

    def update_border_times(self, task: Task) -> Literal[1]:
        t = ClockObject.get_global_clock().get_frame_time()

        for node_list in self.border_nodes.values():
            for n in node_list:
                if hasattr(n, "set_shader_input"):
                    n.set_shader_input("time", t)  # type: ignore

        return task.cont

    def update_borders(self) -> None:
        for p in PlayerManager.all().values():
            pid = p.id
            if pid is None:
                continue

            for n in self.border_nodes.get(pid, []):
                n.remove_node()

            self.border_nodes[pid] = self._create_empire_border_hexes(p)

        MessengerGlobal.messenger.send("ui.borders.updated")

    def _iter_exposed_border_edges(
        self,
        x: int,
        y: int,
        territory: Set[Tuple[int, int]],
        z_offset: float,
    ) -> List[Tuple[LVecBase3f, LVecBase3f]]:
        edges: List[Tuple[LVecBase3f, LVecBase3f]] = []

        for edge_index, (dx, dy) in enumerate(self.HEX_DIRECTIONS[x % 2]):
            if (x + dx, y + dy) in territory:
                continue

            edges.append(self._get_world_edge_points(x, y, edge_index, z_offset))

        return edges

    def _get_world_edge_points(
        self,
        x: int,
        y: int,
        edge_index: int,
        z_offset: float,
    ) -> Tuple[LVecBase3f, LVecBase3f]:
        wx, wy, wz = TileRepository.hex_to_world(x, y)
        z = wz + z_offset

        start_angle = math.radians(60.0 * edge_index)
        end_angle = math.radians(60.0 * (edge_index + 1))

        start = LVecBase3f(
            wx + math.cos(start_angle) * self.BORDER_RADIUS,
            wy + math.sin(start_angle) * self.BORDER_RADIUS,
            z,
        )
        end = LVecBase3f(
            wx + math.cos(end_angle) * self.BORDER_RADIUS,
            wy + math.sin(end_angle) * self.BORDER_RADIUS,
            z,
        )

        return start, end

    def _append_dashed_edge(
        self,
        segs: LineSegs,
        start: LVecBase3f,
        end: LVecBase3f,
    ) -> None:
        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z

        edge_length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if edge_length <= 0.0:
            return

        direction = LVecBase3f(dx / edge_length, dy / edge_length, dz / edge_length)
        cursor = 0.0

        while cursor < edge_length:
            dash_end = min(cursor + self.BORDER_DASH_VISIBLE_LENGTH, edge_length)

            dash_start_point = LVecBase3f(
                start.x + direction.x * cursor,
                start.y + direction.y * cursor,
                start.z + direction.z * cursor,
            )
            dash_end_point = LVecBase3f(
                start.x + direction.x * dash_end,
                start.y + direction.y * dash_end,
                start.z + direction.z * dash_end,
            )

            segs.move_to(dash_start_point)
            segs.draw_to(dash_end_point)

            cursor += self.BORDER_DASH_LENGTH

    def _soft_player_color(self, color: Tuple4f, alpha: float) -> Tuple4f:
        r, g, b, _ = color
        blend_r, blend_g, blend_b = self.BORDER_WORLD_BLEND_COLOR
        player_weight = self.BORDER_PLAYER_COLOR_WEIGHT
        world_weight = 1.0 - player_weight

        return (
            self._clamp01((r * player_weight) + (blend_r * world_weight)),
            self._clamp01((g * player_weight) + (blend_g * world_weight)),
            self._clamp01((b * player_weight) + (blend_b * world_weight)),
            self._clamp01(alpha),
        )

    def _lighten_color(self, color: Tuple4f, alpha: float) -> Tuple4f:
        r, g, b, _ = color

        return (
            self._clamp01((r * 0.72) + 0.28),
            self._clamp01((g * 0.72) + 0.28),
            self._clamp01((b * 0.72) + 0.28),
            self._clamp01(alpha),
        )

    def _clamp01(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _get_border_edge_flags(
        self,
        x: int,
        y: int,
        territory: Set[Tuple[int, int]],
    ) -> BorderEdgeFlags:
        flags: List[float] = []

        for dx, dy in self.HEX_DIRECTIONS[x % 2]:
            flags.append(0.0 if (x + dx, y + dy) in territory else 1.0)

        return (
            flags[0],
            flags[1],
            flags[2],
            flags[3],
            flags[4],
            flags[5],
        )

    def _has_visible_border_edge(self, edge_flags: BorderEdgeFlags) -> bool:
        return any(edge_flag > 0.5 for edge_flag in edge_flags)

    def _edge_flags_to_mask(self, edge_flags: BorderEdgeFlags) -> int:
        mask = 0

        for i, edge_flag in enumerate(edge_flags):
            if edge_flag > 0.5:
                mask |= 1 << i

        return mask

    def _get_border_mask(self, x: int, y: int, territory: Set[Tuple[int, int]]) -> int:
        return self._edge_flags_to_mask(self._get_border_edge_flags(x, y, territory))

    def _get_world_edge_mask(self, x: int, y: int) -> int:
        from managers.world import World

        mask = 0
        grid = World.get_singleton_instance().get_grid()
        here = grid[(x, y)].terrain_type  # type: ignore

        for i, (dx, dy) in enumerate(self.HEX_DIRECTIONS[x % 2]):
            neigh = grid.get((x + dx, y + dy))
            if neigh is None or neigh.terrain_type != here:  # type: ignore
                mask |= 1 << i

        return mask
