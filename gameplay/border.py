import math
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Set, Tuple

from PIL import Image
from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from panda3d.core import (
    ClockObject,
    LVecBase3f,
    LVecBase4f,
    PNMImage,
    Shader,  # type: ignore
    StringStream,  # type: ignore
    Texture,  # type: ignore
    TransparencyAttrib,  # type: ignore
    NodePath,
)
from direct.task.Task import Task

from gameplay.repositories.tile import TileRepository
from helpers.cache import Cache
from helpers.geometry import generate_flat_top_hex

from managers.player import PlayerManager
from managers.world import World
from system.shaders import Shaders
from helpers.colors import Colors, Tuple4f

if TYPE_CHECKING:
    from gameplay.player import Player

import io


class Borders(DirectObject):
    HEX_DIRECTIONS = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)]

    COLOR_HEX_TOP_BORDERS = Colors.MAGENTA
    COLOR_HEX_WALLS = Colors.BLACK
    TOP_BORDER_SCALE = 1.0
    TOP_BORDER_EMPIRE_SCALE = 0.98

    def __init__(
        self,
        map_size: Tuple[int, int],
        shader_system: Shaders,
        parent: NodePath,
    ):
        self.map_width, self.map_height = map_size
        self.shader_system = shader_system
        self.parent = parent

        self.border_nodes: Dict[str, List[NodePath]] = {}
        self.border_textures: Dict[str, Texture] = {}

        self.logger = Cache.get_showbase_instance().logger.get_singleton_instance().graphics.getChild("borders")

        self.shader = self.shader_system.load_shader(
            "borders",
            "assets/shaders/border.vert",
            "assets/shaders/border_ring.frag",
        )
        self.hex_border_shader: Shader = self.shader_system.load_shader(
            "hex_borders",
            "assets/shaders/hex_border.vert",
            "assets/shaders/hex_border.frag",
        )

        # create a threaded TaskChain named "borders"
        Cache.get_showbase_instance().taskMgr.setupTaskChain("borders", numThreads=1)

        # listen for async-mask completion
        self.accept("borders.task_done", self._on_task_done)

        # initial build + event hooks
        self.setup_borders()
        self.register()

    def register(self) -> None:
        # update time uniform on main chain
        Cache.get_showbase_instance().taskMgr.add(self.update_border_times, "update_border_shader_times", delay=5)
        self.accept("game.border.refresh", self.refresh)

    def setup_borders(self) -> None:
        self.reset()

        # - - This was creating so many nodes that it was causing performance issues - -
        # world-mask stays sync (optional to thread similarly)
        # self.hex_border_tex = self.generate_world_border_mask(
        #    map_size=(self.map_width, self.map_height),
        #    hex_radius_px=50,
        # )

        # clear old textures
        for tex in self.border_textures.values():
            tex.release_all()
        self.border_textures.clear()

        # kick off async player-mask builds
        for p in PlayerManager.all().values():
            self._enqueue_player(p)

        # - - This was creating so many nodes that it was causing performance issues - -
        # draw world outlines
        # self.apply_shader_to_hexes(self.generate_world_border_nodes())

    def refresh(self, *args: Any) -> None:
        self.reset()
        self.border_textures.clear()
        for p in PlayerManager.all().values():
            self._enqueue_player(p)

        # reapply world-mask & nodes
        # self.hex_border_tex = self.generate_world_border_mask(
        #    map_size=(self.map_width, self.map_height), hex_radius_px=50
        # )
        # self.apply_shader_to_hexes(self.generate_world_border_nodes())
        MessengerGlobal.messenger.send("ui.borders.updated")

    def reset(self) -> None:
        for nodes in self.border_nodes.values():
            for node in nodes:
                node.remove_node()
        self.border_nodes.clear()

    def _enqueue_player(self, player: "Player") -> None:
        owned = set(player.get_all_tiles())
        growing = set(player.get_all_tiles_marked_for_border_growth())
        task_name = f"generate_border_mask_{player.id}"
        Cache.get_showbase_instance().taskMgr.add(
            self._async_mask_task,
            task_name,
            extraArgs=[player.id, owned, growing],
            appendTask=False,
            taskChain="borders",
        )

    def _async_mask_task(
        self,
        player_id: str,
        owned: Set[Tuple[int, int]],
        growing: Set[Tuple[int, int]],
    ) -> bool:
        """Runs off-thread: builds PNMImage and sends it back on 'borders.task_done'."""
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
        """Main-thread: convert mask → Texture, rebuild hexes, fire UI update."""
        tex = Texture(f"border_mask_{player_id}")
        tex.load(mask)
        tex.set_magfilter(Texture.FT_nearest)
        tex.set_minfilter(Texture.FT_nearest)
        self.border_textures[player_id] = tex

        # replace that player’s hex nodes
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
        # collect all owned/growing tiles into self.player_tiles
        cols, rows = map_size
        player_tiles: Set[Tuple[int, int]] = set()
        for player in PlayerManager.all().values():
            tiles_p = set(player.get_all_tiles().keys()) | set(player.get_all_tiles_marked_for_border_growth().keys())
            player_tiles.update(tiles_p)
        self.player_tiles = player_tiles

        # compute image dimensions
        r = hex_radius_px
        w = 2 * r
        h = int(math.sqrt(3) * r)
        horiz = int(1.5 * r)
        vert = h
        img_w = horiz * (cols - 1) + w
        img_h = vert * rows + r

        # build PIL image entirely in memory
        img = Image.new("RGB", (img_w, img_h), bg_color)

        # convert PIL → PNMImage via an in-memory buffer
        pnm = PNMImage()
        with io.BytesIO() as buf:
            img.save("/tmp/temp_image.png", format="PNG")  # Save to a temp file for debugging
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
        self.world_hexes: List[NodePath] = []
        grid = World.get_singleton_instance().get_grid()
        hex_model = generate_flat_top_hex()
        for x, y in grid:
            np = hex_model.copy_to(self.parent)
            np.set_scale(self.TOP_BORDER_SCALE)
            wx, wy, wz = TileRepository.hex_to_world(x, y)
            np.set_pos(LVecBase3f(wx, wy, wz + 0.030))
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
        nodes: List[NodePath] = []
        for x, y in player.get_all_tiles():
            np = generate_flat_top_hex().copy_to(self.parent)
            np.set_scale(self.TOP_BORDER_EMPIRE_SCALE)
            wx, wy, wz = TileRepository.hex_to_world(x, y)
            np.set_pos(LVecBase3f(wx, wy, wz + 0.07))
            np.set_hpr(30, 0, 0)

            tex = self.border_textures.get(player.id)  # type: ignore
            if not tex:
                self.logger.error(f"[Borders] No texture for player {player.id}")
                continue

            np.set_shader(self.shader)
            np.set_shader_input("borderColor", LVecBase4f(*player.color))  # type: ignore
            np.set_shader_input("borderMask", tex)  # type: ignore
            np.set_shader_input("tilePos", (x, y))  # type: ignore
            np.set_shader_input("mapSize", (self.map_width, self.map_height))  # type: ignore
            np.set_shader_input("time", ClockObject.get_global_clock().get_frame_time())  # type: ignore

            np.set_transparency(TransparencyAttrib.M_alpha)
            np.set_bin("fixed", 40)
            np.set_depth_write(False)
            np.set_depth_test(True)
            np.set_two_sided(True)
            np.set_scale(1)

            nodes.append(np)
        return nodes

    def update_border_times(self, task: Task) -> Literal[1]:
        t = ClockObject.get_global_clock().get_frame_time()
        for node_list in self.border_nodes.values():
            for n in node_list:
                n.set_shader_input("time", t)  # type: ignore
        return task.cont

    def update_borders(self) -> None:
        for p in PlayerManager.all().values():
            pid = p.id
            for n in self.border_nodes.get(pid, []):  # type: ignore
                n.remove_node()  # type: ignore
            self.border_nodes[pid] = self._create_empire_border_hexes(p)  # type: ignore
        MessengerGlobal.messenger.send("ui.borders.updated")

    def _get_border_mask(self, x: int, y: int, player: "Player") -> int:
        mask = 0
        for i, (dx, dy) in enumerate(self.HEX_DIRECTIONS + [(0, 0)]):
            if not player.owns_tile(x + dx, y + dy):
                mask |= 1 << i
        return mask

    def _get_world_edge_mask(self, x: int, y: int) -> int:
        """bit i is set if neighbor in direction i is a different terrain."""
        mask = 0
        grid = World.get_singleton_instance().get_grid()
        here = grid[(x, y)].terrain_type  # type: ignore
        for i, (dx, dy) in enumerate(self.HEX_DIRECTIONS):
            neigh = grid.get((x + dx, y + dy))
            # outside map or different type → draw that side
            if neigh is None or neigh.terrain_type != here:  # type: ignore
                mask |= 1 << i
        return mask
