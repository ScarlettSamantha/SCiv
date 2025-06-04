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

        # player_id -> list of NodePath
        self.border_nodes: Dict[str, List[NodePath]] = {}
        # player_id -> Texture
        self.border_textures: Dict[str, Texture] = {}

        self.logger = Cache.get_showbase_instance().logger.get_singleton_instance().graphics.getChild("borders")

        self.shader = self.shader_system.load_shader(  # type: ignore
            "borders",
            "assets/shaders/border.vert",
            "assets/shaders/border_ring.frag",
        )
        self.hex_border_shader: Shader = self.shader_system.load_shader(  # type: ignore
            "hex_borders",
            "assets/shaders/hex_border.vert",
            "assets/shaders/hex_border.frag",
        )

        self.player_tiles: Set[Tuple[int, int]] = set()

        self.setup_borders()
        self.register()

    def register(self) -> None:
        # update time uniform periodically
        self.addTask(self.update_border_times, "update_border_shader_times", delay=5)  # type: ignore
        self.accept("game.gameplay.city.grows_population", self.refresh)
        self.accept("game.border.refresh", self.refresh)

    def setup_borders(self) -> None:
        self.reset()

        # build a single world mask matching our actual map_size
        self.hex_border_tex = self.generate_world_border_mask(  # type: ignore
            map_size=(self.map_width, self.map_height),
            hex_radius_px=50,
        )

        # clear any old player textures
        for tex in self.border_textures.values():  # type: ignore
            tex.release_all()  # type: ignore
        self.border_textures.clear()  # type: ignore

        # generate player-specific borders
        players = list(PlayerManager.all().values())
        for p in players:
            p_id = p.id
            if p_id is None:
                self.logger.error(f"[Borders] Player {p_id} has no ID")
                continue
            self.border_textures[p_id] = self._generate_player_border_texture(p)  # type: ignore
            self.border_nodes[p_id] = self._create_empire_border_hexes(p)

        # sanity check shader loaded
        if not self.hex_border_shader:  # type: ignore
            self.logger.error("Failed to load hex_border shader")
            print(self.hex_border_shader.get_last_error())  # type: ignore

        # draw world‐wide hex outlines (red blips)
        self.apply_shader_to_hexes(self.generate_world_border_nodes())

    def refresh(self, *args: Any) -> None:
        self.reset()
        self.border_textures.clear()  # type: ignore

        players = list(PlayerManager.all().values())
        for p in players:
            p_id = p.id
            if p_id is None:
                self.logger.error(f"[Borders] Player {p_id} has no ID")
                continue
            self.border_textures[p_id] = self._generate_player_border_texture(p)  # type: ignore
            self.border_nodes[p_id] = self._create_empire_border_hexes(p)

        # reapply world nodes each refresh
        self.hex_border_tex = self.generate_world_border_mask(  # type: ignore
            map_size=(self.map_width, self.map_height), hex_radius_px=50
        )
        self.apply_shader_to_hexes(self.generate_world_border_nodes())

        MessengerGlobal.messenger.send("ui.borders.updated")

    def reset(self) -> None:
        for nodes in self.border_nodes.values():
            for node in nodes:
                node.remove_node()  # type: ignore
        self.border_nodes.clear()

    def _generate_player_border_texture(self, player: "Player") -> Texture:  # type: ignore
        mask = PNMImage(self.map_width, self.map_height, 3)
        mask.fill(0)  # type: ignore

        owned = player.get_all_tiles()
        growing = player.get_all_tiles_marked_for_border_growth()
        self.logger.debug(f"[Borders] Player {player.id} controls {len(owned)} tiles")

        for x, y in owned:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_red(x, y, 1.0)  # type: ignore
        for x, y in growing:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_green(x, y, 1.0)  # type: ignore

        mask.flip(False, True, False)  # type: ignore

        tex: Texture = Texture(f"border_mask_{player.id}")  # type: ignore
        tex.load(mask)  # type: ignore
        tex.set_magfilter(Texture.FT_nearest)  # type: ignore
        tex.set_minfilter(Texture.FT_nearest)  # type: ignore
        return tex  # type: ignore

    def generate_world_border_mask(  # type: ignore
        self,
        map_size: Tuple[int, int] = (25, 25),
        hex_radius_px: int = 50,
        bg_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> Texture:
        cols, rows = map_size
        player_tiles: Set[Tuple[int, int]] = set()
        for player in PlayerManager.all().values():
            tiles_player = set(player.get_all_tiles().keys()) | set(
                player.get_all_tiles_marked_for_border_growth().keys()
            )
            player_tiles.update(tiles_player)
        self.player_tiles = player_tiles

        r = hex_radius_px
        w = 2 * r
        h = int(math.sqrt(3) * r)
        horiz = int(1.5 * r)
        vert = h

        img_w = horiz * (cols - 1) + w
        img_h = vert * rows + r
        img = Image.new("RGB", (img_w, img_h), bg_color)

        img.save("hex_border_mask.png")

        tex: Texture = Texture("hex_border_mask.png")  # type: ignore
        pnm: PNMImage = PNMImage()
        with io.BytesIO() as buf:
            img.save(buf, format="PNG")
            buf.seek(0)
            stream: StringStream = StringStream(buf.getvalue())  # type: ignore
            pnm.read(stream)  # type: ignore

        tex.load(pnm)  # type: ignore
        tex.set_magfilter(Texture.FT_nearest)  # type: ignore
        tex.set_minfilter(Texture.FT_nearest)  # type: ignore
        return tex  # type: ignore

    def generate_world_border_nodes(self) -> List[NodePath]:
        self.world_hexes: List[NodePath] = []

        # iterate every tile in the world
        grid = World.get_singleton_instance().get_grid()
        hex = generate_flat_top_hex()
        for x, y in grid:
            hex_np: NodePath = hex.copy_to(self.parent)  # type: ignore
            hex_np.set_scale(self.TOP_BORDER_SCALE)  # type: ignore

            # position it just above the terrain
            wx, wy, wz = TileRepository.hex_to_world(x, y)
            hex_np.set_pos(LVecBase3f(wx, wy, wz + 0.030))  # type: ignore
            hex_np.set_hpr(30, 0, 0)  # type: ignore

            self.world_hexes.append(hex_np)  # type: ignore
        return self.world_hexes

    def apply_shader_to_hex(self, hex_node: NodePath, color: Tuple4f = COLOR_HEX_TOP_BORDERS) -> None:
        hex_node.set_shader(self.hex_border_shader)  # type: ignore
        hex_node.set_shader_input("borderMask", self.hex_border_tex)  # type: ignore
        hex_node.set_shader_input("borderColor", *color)  # type: ignore
        hex_node.set_shader_input("tilePos", (0, 0))  # type: ignore
        hex_node.set_shader_input("mapSize", (self.map_width, self.map_height))  # type: ignore
        hex_node.set_shader_input("edgeMask", 63)  # type: ignore

    def apply_shader_to_hexes(self, hex_nodes: List[NodePath]) -> None:
        for node in hex_nodes:
            self.apply_shader_to_hex(node, self.COLOR_HEX_WALLS)

    def _create_empire_border_hexes(self, player: "Player") -> List[NodePath]:
        hex_nodes: List[NodePath] = []
        for x, y in player.get_all_tiles():
            hex_np: NodePath = generate_flat_top_hex().copy_to(self.parent)  # type: ignore
            hex_np.set_scale(self.TOP_BORDER_EMPIRE_SCALE)  # type: ignore

            pos = TileRepository.hex_to_world(x, y)
            hex_np.set_pos(LVecBase3f(pos[0], pos[1], pos[2] + 0.07))  # type: ignore
            hex_np.set_hpr(30, 0, 0)  # type: ignore

            tex = self.border_textures.get(player.id)  # type: ignore
            if tex is None:
                self.logger.error(f"[Borders] No texture for player {player.id}")
                continue

            hex_np.set_shader(self.shader)  # type: ignore
            hex_np.set_shader_input("borderColor", LVecBase4f(*player.color))  # type: ignore
            hex_np.set_shader_input("borderMask", tex)  # type: ignore
            hex_np.set_shader_input("tilePos", (x, y))  # type: ignore
            hex_np.set_shader_input("mapSize", (self.map_width, self.map_height))  # type: ignore
            hex_np.set_shader_input("time", ClockObject.get_global_clock().get_frame_time())  # type: ignore

            hex_np.set_transparency(TransparencyAttrib.M_alpha)  # type: ignore
            hex_np.set_bin("fixed", 40)  # type: ignore
            hex_np.set_depth_write(False)  # type: ignore
            hex_np.set_depth_test(True)  # type: ignore
            hex_np.set_two_sided(True)  # type: ignore
            hex_np.set_scale(1)  # type: ignore

            hex_nodes.append(hex_np)  # type: ignore
        return hex_nodes

    def update_border_times(self, task: Task) -> Literal[1]:
        t = ClockObject.get_global_clock().get_frame_time()
        for nodes in self.border_nodes.values():
            for node in nodes:
                node.set_shader_input("time", t)  # type: ignore
        return task.cont

    def update_borders(self) -> None:
        for p in PlayerManager.all().values():
            pid = p.id
            for node in self.border_nodes.get(pid, []):  # type: ignore
                node.remove_node()  # type: ignore
            self.border_nodes[pid] = self._create_empire_border_hexes(p)  # type: ignore
        # world-update if needed
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
