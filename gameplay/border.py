from typing import TYPE_CHECKING, Any, Dict, List, Literal, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import (
    ClockObject,
    LVecBase4f,
    NodePath,
    PNMImage,
    Texture,
    TransparencyAttrib,
)

from gameplay.repositories.tile import TileRepository
from helpers.cache import Cache
from helpers.geometry import generate_flat_top_hex
from managers.player import PlayerManager
from system.shaders import Shaders

if TYPE_CHECKING:
    from gameplay.player import Player


class Borders(DirectObject):
    HEX_DIRECTIONS = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)]

    def __init__(self, map_size: Tuple[int, int], shader_system: Shaders, parent: NodePath):
        self.map_width, self.map_height = map_size
        self.shader_system = shader_system
        self.parent = parent
        self.border_nodes: Dict[str | None, NodePath | List[NodePath]] = {}  # player_id -> NodePath
        self.border_textures: Dict[str | None, NodePath] = {}  # player_id -> Texture
        self.tile_repository = TileRepository
        self.logger = Cache.get_showbase_instance().logger.get_singleton_instance().graphics.getChild("borders")

        self.shader = self.shader_system.load_shader(  # type: ignore
            "borders", "assets/shaders/border.vert", "assets/shaders/border_ring.frag"
        )

        self.setup_borders()
        self.register()

    def register(self):
        self.addTask(self.update_border_times, "update_border_shader_times", delay=5)
        self.accept("game.gameplay.city.gets_tile_ownership", self.refresh)
        self.accept("game.gameplay.city.grows_population", self.refresh)
        self.accept("game.border.refresh", self.refresh)

    def refresh(self, *args: Any):
        self.reset()
        self.border_textures.clear()
        players = list(PlayerManager.all().values())

        for player in players:
            texture = self._generate_border_texture(player)
            self.border_textures[player.id] = texture

        for player in players:
            nodes = self._create_border_hexes(player)
            self.border_nodes[player.id] = nodes

        MessengerGlobal.messenger.send("ui.borders.updated")

    def reset(self):
        # Remove all existing border nodes from scene
        for nodes in self.border_nodes.values():
            if isinstance(nodes, list):
                for node in nodes:  # type: ignore
                    node.remove_node()  # type: ignore
            elif isinstance(nodes, NodePath):  # type: ignore
                nodes.remove_node()  # type: ignore

        self.border_nodes.clear()

    def setup_borders(self):
        self.reset()

        # Optionally free old textures
        for tex in self.border_textures.values():
            tex.release_all()  # type: ignore
        self.border_textures.clear()

        players = list(PlayerManager.all().values())

        for player in players:
            texture = self._generate_border_texture(player)
            self.border_textures[player.id] = texture

        for player in players:
            nodes = self._create_border_hexes(player)
            self.border_nodes[player.id] = nodes

    def _generate_border_texture(self, player: "Player") -> Texture:
        mask = PNMImage(self.map_width, self.map_height, 3)
        mask.fill(0)  # type: ignore

        tiles = player.get_all_tiles()
        next_tiles = player.get_all_tiles_marked_for_border_growth()
        self.logger.debug(f"[Borders] Player {player.id} controls {len(tiles)} tiles")

        for x, y in tiles:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_red(x, y, 1.0)  # type: ignore

        for x, y in next_tiles:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                mask.set_green(x, y, 1.0)  # type: ignore

        mask.flip(False, True, False)  # Flip vertically (y-axis) # type: ignore

        tex = Texture(f"border_mask_{player.id}")
        tex.load(mask)  # type: ignore
        tex.set_magfilter(Texture.FT_nearest)  # type: ignore
        tex.set_minfilter(Texture.FT_nearest)  # type: ignore
        return tex

    def _create_border_hexes(self, player: "Player") -> list[NodePath]:
        hex_nodes = []

        for x, y in player.get_all_tiles():
            hex_np: NodePath = generate_flat_top_hex().copy_to(self.parent)  # type: ignore
            hex_np.set_scale(1.0)  # type: ignore

            world_pos = self.hex_to_world(x, y)
            hex_np.set_pos(world_pos)  # type: ignore
            hex_np.set_hpr(30, 0, 0)  # type: ignore

            edge_mask = self._get_border_mask(x, y, player)  # type: ignore

            tex = self.border_textures.get(player.id)
            if tex is None:
                self.logger.error(f"[Borders] Warning: no border texture for player {player.id}")
                continue

            # Assign shader and inputs
            hex_np.set_shader(self.shader)  # type: ignore
            hex_np.set_shader_input("borderColor", LVecBase4f(*player.color))  # type: ignore
            hex_np.set_shader_input("borderMask", tex)  # type: ignore
            hex_np.set_shader_input("tilePos", (x, y))  # type: ignore
            hex_np.set_shader_input("mapSize", (self.map_width, self.map_height))  # type: ignore
            hex_np.set_shader_input("time", ClockObject.get_global_clock().get_frame_time())  # type: ignore
            self.logger.debug(f"[ShaderInput] tilePos: {(x, y)}, mapSize: {(self.map_width, self.map_height)}")  # type: ignore

            # Visual setup
            hex_np.set_transparency(TransparencyAttrib.M_alpha)  # type: ignore
            hex_np.set_bin("fixed", 0)  # type: ignore
            hex_np.set_depth_write(False)  # type: ignore
            hex_np.set_depth_test(True)  # type: ignore
            hex_np.set_two_sided(True)  # type: ignore
            hex_np.set_scale(0.49)  # type: ignore

            hex_nodes.append(hex_np)  # type: ignore

        return hex_nodes  # type: ignore

    def update_border_times(self, task: Task) -> Literal[1]:
        current_time = ClockObject.get_global_clock().get_frame_time()
        for player_hexes in self.border_nodes.values():
            for node in player_hexes:  # type: ignore
                node.set_shader_input("time", current_time)  # type: ignore
        return task.cont

    def update_borders(self):
        for player in PlayerManager.all().values():
            player_id = player.id

            # Remove old hexes
            for node in self.border_nodes.get(player_id, []):  # type: ignore
                node.remove_node()  # type: ignore

            # Create updated hexes
            new_nodes = self._create_border_hexes(player)
            self.border_nodes[player_id] = new_nodes

        MessengerGlobal.messenger.send("ui.borders.updated")

    def hex_to_world(self, x: int, y: int) -> Tuple[float, float, float]:
        tile = self.tile_repository.get_tile(x, y)
        if tile:
            pos = tile.get_node().get_pos()  # type: ignore
            return (pos.x, pos.y, pos.z + 0.075)  # Raise slightly for overlay# type: ignore
        return (0, 0, 0)

    def _get_border_mask(self, x: int, y: int, player: "Player") -> int:
        mask = 0
        for i, (dx, dy) in enumerate(self.HEX_DIRECTIONS):
            nx, ny = x + dx, y + dy
            if not player.owns_tile(nx, ny):
                mask |= 1 << i
        return mask
