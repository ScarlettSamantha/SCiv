import math
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Set, Tuple, cast

from gameplay.vision import VisionTileState
from panda3d.core import (
    BitMask32,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
    PandaNode,
    TransparencyAttrib,
)

from helpers.colors import Colors

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay._units import Units
    from gameplay.unit import Unit
    from system.tile_grid import TileModelGrid
    from system.renderers.tile_renderer import TileRenderer
    from system.tile_renderer import TileRendererSystem
    from system.renderers.landmass_label_overlay import LandmassLabelOverlay


FOGGED_TILE_TINT: Tuple[float, float, float, float] = Colors.GAMEPLAY_FOGGED_TILE_TINT
UNSEEN_TILE_TINT: Tuple[float, float, float, float] = Colors.GAMEPLAY_UNSEEN_TILE_TINT
FOG_BLOB_TOP_COLOR: Tuple[float, float, float, float] = Colors.GAMEPLAY_FOG_BLOB_TOP_COLOR
FOG_BLOB_WALL_COLOR: Tuple[float, float, float, float] = Colors.GAMEPLAY_FOG_BLOB_WALL_COLOR
FOG_BLOB_TOP_Z_OFFSET: float = 0.045
FOG_BLOB_WALL_DEPTH: float = 1.75

class FogBlobOverlay:
    EDGE_NEIGHBOR_OFFSETS_EVEN_Q: Tuple[Tuple[int, int], ...] = (
        (0, 1),
        (1, 0),
        (1, -1),
        (0, -1),
        (-1, -1),
        (-1, 0),
    )
    EDGE_NEIGHBOR_OFFSETS_ODD_Q: Tuple[Tuple[int, int], ...] = (
        (0, 1),
        (1, 1),
        (1, 0),
        (0, -1),
        (-1, 0),
        (-1, 1),
    )

    def __init__(
        self,
        *,
        parent: NodePath,
        radius: float = 1.0,
        top_color: Tuple[float, float, float, float] = FOG_BLOB_TOP_COLOR,
        wall_color: Tuple[float, float, float, float] = FOG_BLOB_WALL_COLOR,
        top_z_offset: float = FOG_BLOB_TOP_Z_OFFSET,
        wall_depth: float = FOG_BLOB_WALL_DEPTH,
    ) -> None:
        self.radius = float(radius)
        self.top_color = top_color
        self.wall_color = wall_color
        self.top_z_offset = float(top_z_offset)
        self.wall_depth = float(wall_depth)
        self.root: NodePath = parent.attachNewNode(PandaNode("fog_blob_overlay"))
        self.root.setTransparency(TransparencyAttrib.M_alpha)
        self.root.setDepthWrite(False)
        self.root.setDepthTest(True)
        self.root.setBin("fixed", 76)
        self.root.setCollideMask(BitMask32.allOff())
        self.root.setTwoSided(True)
        self._disable_collision(self.root)
        self._geom_np: NodePath | None = None

    def set_radius(self, radius: float) -> None:
        self.radius = float(radius)

    def clear(self) -> None:
        if self._geom_np is not None and not self._geom_np.isEmpty():
            self._geom_np.removeNode()

        self._geom_np = None
        self.root.getChildren().detach()

    def dispose(self) -> None:
        self.clear()

        if not self.root.isEmpty():
            self.root.removeNode()

    def sync_fogged_tiles(self, tiles: Iterable["Tile"]) -> None:
        cached_tiles = list(tiles)
        self.clear()

        if not cached_tiles:
            return

        fogged_coords = {(int(tile.get_tile().x), int(tile.get_tile().y)) for tile in cached_tiles}
        geom_node = self._build_geom(cached_tiles, fogged_coords)

        self._geom_np = self.root.attachNewNode(geom_node)
        self._geom_np.setCollideMask(BitMask32.allOff())
        self._geom_np.setDepthWrite(False)
        self._geom_np.setDepthTest(True)
        self._geom_np.setTransparency(TransparencyAttrib.M_alpha)
        self._geom_np.setBin("fixed", 76)
        self._geom_np.setTwoSided(True)
        self._disable_collision(self._geom_np)

    def _disable_collision(self, node: NodePath) -> None:
        node.setCollideMask(BitMask32.allOff())

        panda_node = node.node()

        set_into_collide_mask = getattr(panda_node, "setIntoCollideMask", None)
        if callable(set_into_collide_mask):
            set_into_collide_mask(BitMask32.allOff())

        set_from_collide_mask = getattr(panda_node, "setFromCollideMask", None)
        if callable(set_from_collide_mask):
            set_from_collide_mask(BitMask32.allOff())

        for child in node.getChildren():
            self._disable_collision(child)

    def _build_geom(self, tiles: List["Tile"], fogged_coords: Set[Tuple[int, int]]) -> GeomNode:
        fmt = GeomVertexFormat.get_v3c4()
        vdata = GeomVertexData("fog_blob_overlay_vdata", fmt, Geom.UH_static)
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        color_writer = GeomVertexWriter(vdata, "color")
        triangles = GeomTriangles(Geom.UH_static)
        vertex_count = 0

        def add_vertex(x: float, y: float, z: float, color: Tuple[float, float, float, float]) -> int:
            nonlocal vertex_count

            vertex_writer.addData3f(float(x), float(y), float(z))
            color_writer.addData4f(float(color[0]), float(color[1]), float(color[2]), float(color[3]))
            index = vertex_count
            vertex_count += 1
            return index

        for fog_tile in tiles:
            tile: Tile = fog_tile.get_tile()
            center_x, center_y, top_z = self._tile_center(tile=tile)
            top_z += self.top_z_offset
            corners: List[Tuple[float, float, float]] = self._corners(center_x, center_y, top_z)
            center_index = add_vertex(center_x, center_y, top_z, self.top_color)

            for corner_index in range(6):
                next_corner_index = (corner_index + 1) % 6
                a: int = add_vertex(corners[corner_index][0], corners[corner_index][1], top_z, self.top_color)
                b: int = add_vertex(corners[next_corner_index][0], corners[next_corner_index][1], top_z, self.top_color)
                triangles.addVertices(center_index, a, b)

            tile_coord: Tuple[int, int] = (int(tile.x), int(tile.y))

            for edge_index in range(6):
                neighbor_coord: Tuple[int, int] = self._neighbor_coord_for_edge(tile_coord, edge_index)
                if neighbor_coord in fogged_coords:
                    continue

                self._add_wall_edge(
                    add_vertex=add_vertex,
                    triangles=triangles,
                    corners=corners,
                    edge_index=edge_index,
                    top_z=top_z,
                )

        geom = Geom(vdata)
        geom.addPrimitive(triangles)
        geom_node = GeomNode("fog_blob_overlay_geom")
        geom_node.setIntoCollideMask(BitMask32.allOff())
        geom_node.addGeom(geom)
        return geom_node

    def _add_wall_edge(
        self,
        *,
        add_vertex: Callable[[float, float, float, Tuple[float, float, float, float]], int],
        triangles: GeomTriangles,
        corners: List[Tuple[float, float, float]],
        edge_index: int,
        top_z: float,
    ) -> None:
        next_edge_index = (edge_index + 1) % 6
        ax, ay, _ = corners[edge_index]
        bx, by, _ = corners[next_edge_index]
        bottom_z = top_z - self.wall_depth

        top_a: int = add_vertex(ax, ay, top_z, self.wall_color)
        top_b: int = add_vertex(bx, by, top_z, self.wall_color)
        bottom_b: int = add_vertex(bx, by, bottom_z, self.wall_color)
        bottom_a: int = add_vertex(ax, ay, bottom_z, self.wall_color)

        triangles.addVertices(top_a, bottom_b, top_b)
        triangles.addVertices(top_a, bottom_a, bottom_b)

    def _corners(self, center_x: float, center_y: float, z: float) -> List[Tuple[float, float, float]]:
        corners: List[Tuple[float, float, float]] = []

        for degrees in (120.0, 60.0, 0.0, -60.0, -120.0, 180.0):
            radians = math.radians(degrees)
            corners.append(
                (
                    center_x + self.radius * math.cos(radians),
                    center_y + self.radius * math.sin(radians),
                    z,
                )
            )

        return corners

    def _neighbor_coord_for_edge(self, tile_coord: Tuple[int, int], edge_index: int) -> Tuple[int, int]:
        x, y = tile_coord
        offsets: Tuple[Tuple[int, int], ...] = self.EDGE_NEIGHBOR_OFFSETS_ODD_Q if x % 2 else self.EDGE_NEIGHBOR_OFFSETS_EVEN_Q
        offset_x, offset_y = offsets[edge_index]
        return x + offset_x, y + offset_y

    def _tile_center(self, tile: "Tile") -> Tuple[float, float, float]:
        return tile.calculate_z_pos_on_altitude()


class FogOfWarController:
    def __init__(self) -> None:
        self._synced_player_keys: Set[str] = set()
        self._tile_by_tag: Dict[str, "Tile"] = {}
        self._tile_state_by_tag: Dict[str, VisionTileState] = {}
        self._tile_detail_visibility_by_tag: Dict[str, bool] = {}
        self._unit_visibility_by_key: Dict[str, bool] = {}
        self._last_fog_blob_tile_tags: Set[str] = set()
        self._fog_ceiling_z: float = 0.1
        self._fog_blob_dirty_tile_tags: Set[str] = set()
        self._fog_blob_overlay_synced: bool = False

    def reset(self) -> None:
        self._synced_player_keys.clear()
        self._tile_by_tag.clear()
        self._tile_state_by_tag.clear()
        self._tile_detail_visibility_by_tag.clear()
        self._unit_visibility_by_key.clear()
        self._last_fog_blob_tile_tags.clear()
        self._fog_blob_dirty_tile_tags.clear()
        self._fog_blob_overlay_synced = False
        self._fog_ceiling_z = 0.1

    def sync_tiles(self, tiles: Iterable["Tile"]) -> None:
        self._tile_by_tag = {self._tile_tag(tile): tile for tile in tiles}

    def has_synced_player(self, player: "Player") -> bool:
        return self._player_key(player) in self._synced_player_keys

    def apply(
        self,
        player: "Player",
        tiles: Iterable["Tile"],
        units: Iterable["Unit"],
        *,
        tile_grid: "TileModelGrid | None",
        tile_overlay: "TileRendererSystem",
        label_overlay: "LandmassLabelOverlay | None" = None,
        fog_blob_overlay: "FogBlobOverlay | None" = None,
        changed_tile_tags: Set[str] | None = None,
    ) -> None:
        cached_tiles: List[Tile] = list(tiles)
        player_key: str = self._player_key(player=player)

        if not self._tile_by_tag or player_key not in self._synced_player_keys:
            self.sync_tiles(cached_tiles)

        if changed_tile_tags is not None and player_key in self._synced_player_keys:
            self.apply_changed_tags(
                player=player,
                changed_tile_tags=changed_tile_tags,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                units=units,
                label_overlay=label_overlay,
                fog_blob_overlay=fog_blob_overlay,
                total_tiles=len(cached_tiles),
                rebuild_fog_blob=True,
            )
            return

        fog_ceiling_z: float = self._resolve_fog_ceiling_z(tiles=cached_tiles, tile_grid=tile_grid)
        self._fog_ceiling_z = fog_ceiling_z
        touched_grid = False
        direct_visible_tile_tags: Set[str] = self._get_direct_visible_tile_tags(player=player)

        for tile in cached_tiles:
            tile_tag: str = self._tile_tag(tile=tile)
            state: VisionTileState = player.vision.get_tile_state(tile_or_tag=tile_tag)

            if self._apply_tile_state_if_needed(
                tile,
                state,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                fog_ceiling_z=fog_ceiling_z,
                fog_blob_overlay_enabled=fog_blob_overlay is not None,
                tile_overlay_visible=tile_tag in direct_visible_tile_tags,
                force=player_key not in self._synced_player_keys,
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

        self._sync_fog_blob_overlay(player=player, fog_blob_overlay=fog_blob_overlay)
        self._sync_units(player=player, units=self._collect_units_from_tiles(tiles=cached_tiles, units=units), visible_tile_tags=direct_visible_tile_tags)
        self._sync_label_overlay(player=player, total_tiles=len(cached_tiles), label_overlay=label_overlay)
        self._synced_player_keys.add(player_key)

    def apply_changed_tags(
        self,
        player: "Player",
        changed_tile_tags: Set[str],
        *,
        tile_grid: "TileModelGrid | None",
        tile_overlay: "TileRendererSystem",
        units: Iterable["Unit"] = (),
        all_tiles: Iterable["Tile"] | None = None,
        label_overlay: "LandmassLabelOverlay | None" = None,
        fog_blob_overlay: "FogBlobOverlay | None" = None,
        total_tiles: int | None = None,
        rebuild_fog_blob: bool = True,
    ) -> None:
        cached_units: List[Unit] = list(units)

        if not changed_tile_tags and not cached_units:
            return

        if all_tiles is not None and not self._tile_by_tag:
            cached_tiles: List[Tile] = list(all_tiles)
            self.sync_tiles(cached_tiles)

            if total_tiles is None:
                total_tiles = len(cached_tiles)

        fog_ceiling_z = self._fog_ceiling_z
        touched_grid = False
        changed_tiles: List["Tile"] = []
        direct_visible_tile_tags = self._get_direct_visible_tile_tags(player)

        for tile_tag in changed_tile_tags:
            tile: Tile | None = self._tile_by_tag.get(tile_tag)
            if tile is None:
                continue

            changed_tiles.append(tile)
            state = player.vision.get_tile_state(tile_tag)

            if self._apply_tile_state_if_needed(
                tile,
                state,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                fog_ceiling_z=fog_ceiling_z,
                fog_blob_overlay_enabled=fog_blob_overlay is not None,
                tile_overlay_visible=tile_tag in direct_visible_tile_tags,
                force=True,
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

        if rebuild_fog_blob:
            self._sync_fog_blob_overlay(player=player, fog_blob_overlay=fog_blob_overlay)

        self._sync_units(player=player, units=self._collect_units_from_tiles(tiles=changed_tiles, units=cached_units), visible_tile_tags=direct_visible_tile_tags)

        if label_overlay is not None and total_tiles is not None:
            self._sync_label_overlay(player=player, total_tiles=total_tiles, label_overlay=label_overlay)

        self._synced_player_keys.add(self._player_key(player=player))

    def _collect_units_from_tiles(
        self,
        tiles: Iterable["Tile"],
        units: Iterable["Unit"] = (),
    ) -> List["Unit"]:
        unit_by_key: Dict[str, "Unit"] = {}

        for unit in units:
            unit_by_key[self._unit_key(unit=unit)] = unit

        for tile in tiles:
            tile_units: "Units" = tile.get_tile().get_units()
            for unit in tile_units:
                if not hasattr(unit, "get_tile") or not hasattr(unit, "set_render_visibility"):
                    continue

                resolved_unit: Unit = unit
                unit_by_key[self._unit_key(unit=resolved_unit)] = resolved_unit

        return list(unit_by_key.values())

    def _apply_tile_state_if_needed(
        self,
        tile: "Tile",
        state: VisionTileState,
        *,
        tile_grid: "TileModelGrid | None",
        tile_overlay: "TileRendererSystem",
        fog_ceiling_z: float,
        fog_blob_overlay_enabled: bool,
        tile_overlay_visible: bool,
        force: bool = False,
    ) -> bool:
        tile_tag = self._tile_tag(tile=tile)

        previous_state: VisionTileState | None = self._tile_state_by_tag.get(tile_tag)
        previous_detail_visible: bool | None = self._tile_detail_visibility_by_tag.get(tile_tag)

        if not force and previous_state is state and previous_detail_visible == tile_overlay_visible:
            return False

        previous_fogged: bool = previous_state is not None and self._is_fogged_state(previous_state)
        next_fogged: bool = self._is_fogged_state(state)

        if previous_fogged != next_fogged:
            self._fog_blob_dirty_tile_tags.add(tile_tag)

        grid_changed: bool = False

        if tile_grid is not None and not fog_blob_overlay_enabled:
            previous_unseen: bool = previous_state is None or self._is_unseen_state(previous_state)
            next_unseen: bool = self._is_unseen_state(state)

            if previous_state is None or previous_unseen != next_unseen:
                if next_unseen:
                    tile_grid.hide_tile(tile_or_index=tile)
                else:
                    tile_grid.show_tile(tile_or_index=tile)

                tile_grid.clear_tile_tint(tile_or_index=tile)
                grid_changed = True

        self._tile_state_by_tag[tile_tag] = state
        self._tile_detail_visibility_by_tag[tile_tag] = tile_overlay_visible

        self._apply_renderer_visibility_state(
            tile=tile,
            state=state,
            fog_ceiling_z=fog_ceiling_z,
            fog_blob_overlay_enabled=fog_blob_overlay_enabled,
        )
        self._apply_renderer_detail_visibility_state(tile=tile, visible=tile_overlay_visible)

        if tile_overlay_visible:
            tile_overlay.show_tile(tile)
        else:
            tile_overlay.hide_tile(tile)

        return grid_changed

    def _apply_renderer_detail_visibility_state(self, tile: "Tile", visible: bool) -> None:
        renderer: TileRenderer = tile.renderer
        renderer.set_fog_detail_visibility(visible)

    def _apply_renderer_visibility_state(
        self,
        tile: "Tile",
        state: VisionTileState,
        *,
        fog_ceiling_z: float,
        fog_blob_overlay_enabled: bool,
    ) -> None:
        renderer: TileRenderer = tile.renderer
        renderer.set_fog_ceiling_z(fog_ceiling_z)

        renderer_state: VisionTileState | None = self._renderer_state_for(state, fog_blob_overlay_enabled=fog_blob_overlay_enabled)

        if renderer_state is None:
            return

        renderer.set_visibility_state(renderer_state)

    def _renderer_state_for(
        self,
        state: VisionTileState,
        *,
        fog_blob_overlay_enabled: bool,
    ) -> VisionTileState | None:
        if not fog_blob_overlay_enabled or not self._is_fogged_state(state):
            return state

        visible_state = getattr(VisionTileState, "VISIBLE", None)

        if visible_state is not None:
            return cast(VisionTileState, visible_state)

        return None

    def _sync_fog_blob_overlay(self, player: "Player", fog_blob_overlay: "FogBlobOverlay | None") -> None:
        if fog_blob_overlay is None:
            self._fog_blob_dirty_tile_tags.clear()
            self._fog_blob_overlay_synced = False
            return

        dirty_tile_tags: Set[str] = set(self._fog_blob_dirty_tile_tags)

        if self._fog_blob_overlay_synced and not dirty_tile_tags:
            return

        fogged_tile_tags: Set[str] = self._query_fogged_tile_tags(player)

        if self._fog_blob_overlay_synced and fogged_tile_tags == self._last_fog_blob_tile_tags:
            self._fog_blob_dirty_tile_tags.clear()
            return

        if not fogged_tile_tags:
            self._last_fog_blob_tile_tags.clear()
            self._fog_blob_dirty_tile_tags.clear()
            self._fog_blob_overlay_synced = True
            fog_blob_overlay.clear()
            return

        fogged_tiles: List["Tile"] = []

        for tile_tag in fogged_tile_tags:
            tile: Tile | None = self._tile_by_tag.get(tile_tag)

            if tile is not None:
                fogged_tiles.append(tile)

        self._last_fog_blob_tile_tags = set(fogged_tile_tags)
        self._fog_blob_dirty_tile_tags.clear()
        self._fog_blob_overlay_synced = True
        fog_blob_overlay.sync_fogged_tiles(fogged_tiles)

    def _query_fogged_tile_tags(self, player: "Player") -> Set[str]:
        return self._normalize_tile_tag_values(player.vision.get_fogged_tile_tags())

    def _unit_is_owned_by_player(self, unit: "Unit", player: "Player") -> bool:
        return self._player_key(unit.get_owner()) == self._player_key(player)

    def _sync_units(self, player: "Player", units: Iterable["Unit"], visible_tile_tags: Set[str]) -> None:
        for unit in units:
            unit_key: str = self._unit_key(unit)

            try:
                unit_tile_tag: str = self._tile_tag(unit.get_tile())
                next_visible: bool = unit_tile_tag in visible_tile_tags or self._unit_is_owned_by_player(unit, player)
            except Exception:
                next_visible = self._unit_is_owned_by_player(unit, player)

            if self._unit_visibility_by_key.get(unit_key) == next_visible:
                continue

            self._unit_visibility_by_key[unit_key] = next_visible
            unit.set_render_visibility(next_visible)

    def _sync_label_overlay(
        self,
        player: "Player",
        *,
        total_tiles: int,
        label_overlay: "LandmassLabelOverlay | None" = None,
    ) -> None:
        if label_overlay is None:
            return

        if len(player.vision.get_explored_tile_tags()) == total_tiles:
            label_overlay.root.show()
            return

        label_overlay.root.hide()

    def _resolve_fog_ceiling_z(self, tiles: Iterable["Tile"], tile_grid: "TileModelGrid | None") -> float:
        if tile_grid is not None:
            return float(tile_grid.get_max_world_z()) + 0.1

        return max((float(getattr(tile, "pos_z", 0.0)) for tile in tiles), default=0.0) + 0.1

    def _get_direct_visible_tile_tags(self, player: "Player") -> Set[str]:
        return self._normalize_tile_tag_values(player.vision.get_direct_visible_tile_tags())

    def _normalize_tile_tag_values(self, values: Iterable[Any]) -> Set[str]:
        tile_tags: Set[str] = set()

        for value in values:
            if isinstance(value, str):
                tile_tags.add(value)
                continue

            get_tag = getattr(value, "get_tag", None)

            if callable(get_tag):
                tile_tag = get_tag()

                if isinstance(tile_tag, str) and tile_tag:
                    tile_tags.add(tile_tag)

                continue

            tile_tag = getattr(value, "tag", None)

            if isinstance(tile_tag, str) and tile_tag:
                tile_tags.add(tile_tag)

        return tile_tags

    def _is_unseen_state(self, state: VisionTileState) -> bool:
        if state is VisionTileState.UNSEEN:
            return True

        return self._state_name(state) in {"UNSEEN", "UNKNOWN", "HIDDEN"}

    def _is_fogged_state(self, state: VisionTileState) -> bool:
        return self._state_name(state) in {"FOGGED", "FORGOTTEN", "EXPLORED"}

    def _state_name(self, state: VisionTileState) -> str:
        name = getattr(state, "name", None)

        if isinstance(name, str):
            return name.upper()

        return str(state).split(".")[-1].upper()

    def _player_key(self, player: "Player") -> str:
        return player.get_tag()

    def _unit_key(self, unit: "Unit") -> str:
        return unit.get_tag()

    def _tile_tag(self, tile: "Tile") -> str:
        return tile.get_tag()
