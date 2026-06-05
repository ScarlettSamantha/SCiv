import math
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Protocol, Set, Tuple, cast
from weakref import ReferenceType

from gameplay.vision import VisionTileState, is_visible_for_render
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
from sciv.gameplay._units import Units

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


FOGGED_TILE_TINT: Tuple[float, float, float, float] = (0.08, 0.09, 0.11, 0.28)
UNSEEN_TILE_TINT: Tuple[float, float, float, float] = (0.10, 0.10, 0.13, 1.0)
FOG_BLOB_TOP_COLOR: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.38)
FOG_BLOB_WALL_COLOR: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.72)
FOG_BLOB_TOP_Z_OFFSET: float = 0.045
FOG_BLOB_WALL_DEPTH: float = 1.75


class FogTileLike(Protocol):
    tag: str
    renderer: Any
    tile: ReferenceType["Tile"]

    def get_tag(self) -> str: ...

    def get_tile(self) -> "Tile": ...


class FogUnitLike(Protocol):
    def get_tile(self) -> FogTileLike: ...

    def set_render_visibility(self, visible: bool) -> None: ...


class FogTileGridLike(Protocol):
    def hide_tile(self, tile_or_index: Any) -> None: ...

    def show_tile(self, tile_or_index: Any) -> None: ...

    def set_tile_tint(self, tile_or_index: Any, rgba: Tuple[float, float, float, float]) -> None: ...

    def clear_tile_tint(self, tile_or_index: Any) -> None: ...

    def collect(self) -> None: ...

    def get_max_world_z(self) -> float: ...


class FogTileOverlayLike(Protocol):
    def hide_tile(self, tile: Any) -> None: ...

    def show_tile(self, tile: Any) -> None: ...


class FogLabelOverlayLike(Protocol):
    root: Any


class FogBlobOverlayLike(Protocol):
    def sync_fogged_tiles(self, tiles: Iterable[FogTileLike]) -> None: ...

    def clear(self) -> None: ...


class FogBlobOverlay:
    EDGE_ORDER: Tuple[str, str, str, str, str, str] = ("n", "ne", "se", "s", "sw", "nw")
    EVEN_Q_OFFSETS: Dict[str, Tuple[int, int]] = {
        "n": (0, -1),
        "ne": (1, -1),
        "se": (1, 0),
        "s": (0, 1),
        "sw": (-1, 0),
        "nw": (-1, -1),
    }
    ODD_Q_OFFSETS: Dict[str, Tuple[int, int]] = {
        "n": (0, -1),
        "ne": (1, 0),
        "se": (1, 1),
        "s": (0, 1),
        "sw": (-1, 1),
        "nw": (-1, 0),
    }

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

    def sync_fogged_tiles(self, tiles: Iterable[FogTileLike]) -> None:
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

    def _build_geom(self, tiles: List[FogTileLike], fogged_coords: Set[Tuple[int, int]]) -> GeomNode:
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
            tile = fog_tile.get_tile()
            center_x, center_y, top_z = self._tile_center(tile)
            top_z += self.top_z_offset
            corners = self._corners(center_x, center_y, top_z)
            center_index = add_vertex(center_x, center_y, top_z, self.top_color)

            for corner_index in range(6):
                next_corner_index = (corner_index + 1) % 6
                a = add_vertex(corners[corner_index][0], corners[corner_index][1], top_z, self.top_color)
                b = add_vertex(corners[next_corner_index][0], corners[next_corner_index][1], top_z, self.top_color)
                triangles.addVertices(center_index, a, b)

            tile_coord = (int(tile.x), int(tile.y))
            for edge_index, edge_name in enumerate(self.EDGE_ORDER):
                neighbor_coord = self._neighbor_coord(tile_coord, edge_name)
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

        top_a = add_vertex(ax, ay, top_z, self.wall_color)
        top_b = add_vertex(bx, by, top_z, self.wall_color)
        bottom_b = add_vertex(bx, by, bottom_z, self.wall_color)
        bottom_a = add_vertex(ax, ay, bottom_z, self.wall_color)

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

    def _neighbor_coord(self, tile_coord: Tuple[int, int], edge_name: str) -> Tuple[int, int]:
        x, y = tile_coord
        offsets = self.ODD_Q_OFFSETS if x % 2 else self.EVEN_Q_OFFSETS
        offset_x, offset_y = offsets[edge_name]
        return x + offset_x, y + offset_y

    def _tile_center(self, tile: Any) -> Tuple[float, float, float]:
        get_cords = getattr(tile, "get_cords", None)
        if callable(get_cords):
            coords = get_cords()
            if len(coords) >= 3:
                return float(coords[0]), float(coords[1]), float(coords[2])

        get_pos = getattr(tile, "get_pos", None)
        if callable(get_pos):
            coords = get_pos()
            if len(coords) >= 3:
                return float(coords[0]), float(coords[1]), float(coords[2])

        calculate_z_pos_on_altitude = getattr(tile, "calculate_z_pos_on_altitude", None)
        if callable(calculate_z_pos_on_altitude):
            coords = calculate_z_pos_on_altitude()
            if len(coords) >= 3:
                return float(coords[0]), float(coords[1]), float(coords[2])

        return float(getattr(tile, "pos_x", 0.0)), float(getattr(tile, "pos_y", 0.0)), float(getattr(tile, "pos_z", 0.0))


class FogOfWarController:
    def __init__(self) -> None:
        self._synced_player_keys: Set[str] = set()
        self._tile_by_tag: Dict[str, FogTileLike] = {}
        self._tile_state_by_tag: Dict[str, VisionTileState] = {}
        self._unit_visibility_by_key: Dict[str, bool] = {}
        self._fog_ceiling_z: float = 0.1

    def reset(self) -> None:
        self._synced_player_keys.clear()
        self._tile_by_tag.clear()
        self._tile_state_by_tag.clear()
        self._unit_visibility_by_key.clear()
        self._fog_ceiling_z = 0.1

    def sync_tiles(self, tiles: Iterable[FogTileLike]) -> None:
        self._tile_by_tag = {self._tile_tag(tile): tile for tile in tiles}

    def has_synced_player(self, player: "Player") -> bool:
        return self._player_key(player) in self._synced_player_keys

    def apply(
        self,
        player: "Player",
        tiles: Iterable[FogTileLike],
        units: Iterable[FogUnitLike],
        *,
        tile_grid: FogTileGridLike | None,
        tile_overlay: FogTileOverlayLike,
        label_overlay: FogLabelOverlayLike | None = None,
        fog_blob_overlay: FogBlobOverlayLike | None = None,
        changed_tile_tags: Set[str] | None = None,
    ) -> None:
        cached_tiles = list(tiles)
        player_key = self._player_key(player)

        if not self._tile_by_tag or player_key not in self._synced_player_keys:
            self.sync_tiles(cached_tiles)

        if changed_tile_tags is not None and player_key in self._synced_player_keys:
            self.apply_changed_tags(
                player,
                changed_tile_tags,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                units=units,
                label_overlay=label_overlay,
                fog_blob_overlay=fog_blob_overlay,
                total_tiles=len(cached_tiles),
            )
            return

        fog_ceiling_z = self._resolve_fog_ceiling_z(cached_tiles, tile_grid)
        self._fog_ceiling_z = fog_ceiling_z
        touched_grid = False

        for tile in cached_tiles:
            tile_tag = self._tile_tag(tile)
            state = player.vision.get_tile_state(tile_tag)

            if self._apply_tile_state_if_needed(
                tile,
                state,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                fog_ceiling_z=fog_ceiling_z,
                fog_blob_overlay_enabled=fog_blob_overlay is not None,
                force=player_key not in self._synced_player_keys,
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

        self._sync_fog_blob_overlay(fog_blob_overlay)
        self._sync_units(player, self._collect_units_from_tiles(cached_tiles, units))
        self._sync_label_overlay(player, total_tiles=len(cached_tiles), label_overlay=label_overlay)
        self._synced_player_keys.add(player_key)

    def apply_changed_tags(
        self,
        player: "Player",
        changed_tile_tags: Set[str],
        *,
        tile_grid: FogTileGridLike | None,
        tile_overlay: FogTileOverlayLike,
        units: Iterable[FogUnitLike] = (),
        all_tiles: Iterable[FogTileLike] | None = None,
        label_overlay: FogLabelOverlayLike | None = None,
        fog_blob_overlay: FogBlobOverlayLike | None = None,
        total_tiles: int | None = None,
    ) -> None:
        cached_units = list(units)

        if not changed_tile_tags and not cached_units:
            return

        if all_tiles is not None and not self._tile_by_tag:
            cached_tiles = list(all_tiles)
            self.sync_tiles(cached_tiles)

            if total_tiles is None:
                total_tiles = len(cached_tiles)

        fog_ceiling_z = self._fog_ceiling_z
        touched_grid = False
        changed_tiles: List[FogTileLike] = []

        for tile_tag in changed_tile_tags:
            tile = self._tile_by_tag.get(tile_tag)
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
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

        if changed_tile_tags:
            self._sync_fog_blob_overlay(fog_blob_overlay)

        self._sync_units(player, self._collect_units_from_tiles(changed_tiles, cached_units))

        if label_overlay is not None and total_tiles is not None:
            self._sync_label_overlay(player, total_tiles=total_tiles, label_overlay=label_overlay)

        self._synced_player_keys.add(self._player_key(player))

    def _collect_units_from_tiles(
        self,
        tiles: Iterable[FogTileLike],
        units: Iterable[FogUnitLike] = (),
    ) -> List[FogUnitLike]:
        unit_by_key: Dict[str, FogUnitLike] = {}

        for unit in units:
            unit_by_key[self._unit_key(unit)] = unit

        for tile in tiles:
            tile_units: Units = tile.get_tile().get_units()
            for unit in tile_units:
                if not hasattr(unit, "get_tile") or not hasattr(unit, "set_render_visibility"):
                    continue

                resolved_unit = cast(FogUnitLike, unit)
                unit_by_key[self._unit_key(resolved_unit)] = resolved_unit

        return list(unit_by_key.values())

    def _apply_tile_state_if_needed(
        self,
        tile: FogTileLike,
        state: VisionTileState,
        *,
        tile_grid: FogTileGridLike | None,
        tile_overlay: FogTileOverlayLike,
        fog_ceiling_z: float,
        fog_blob_overlay_enabled: bool,
        force: bool = False,
    ) -> bool:
        tile_tag = self._tile_tag(tile)

        if not force and self._tile_state_by_tag.get(tile_tag) is state:
            return False

        self._tile_state_by_tag[tile_tag] = state

        if tile_grid is not None:
            if self._is_unseen_state(state):
                tile_grid.hide_tile(tile)
            else:
                tile_grid.show_tile(tile)

            tile_grid.clear_tile_tint(tile)

        self._apply_renderer_visibility_state(
            tile,
            state,
            fog_ceiling_z=fog_ceiling_z,
            fog_blob_overlay_enabled=fog_blob_overlay_enabled,
        )

        if is_visible_for_render(state):
            tile_overlay.show_tile(tile)
        else:
            tile_overlay.hide_tile(tile)

        return True

    def _apply_renderer_visibility_state(
        self,
        tile: FogTileLike,
        state: VisionTileState,
        *,
        fog_ceiling_z: float,
        fog_blob_overlay_enabled: bool,
    ) -> None:
        renderer = tile.renderer
        set_fog_ceiling_z = getattr(renderer, "set_fog_ceiling_z", None)
        if callable(set_fog_ceiling_z):
            set_fog_ceiling_z(fog_ceiling_z)

        set_visibility_state = getattr(renderer, "set_visibility_state", None)
        if not callable(set_visibility_state):
            return

        renderer_state = self._renderer_state_for(state, fog_blob_overlay_enabled=fog_blob_overlay_enabled)
        if renderer_state is None:
            return

        set_visibility_state(renderer_state)

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

    def _sync_fog_blob_overlay(self, fog_blob_overlay: FogBlobOverlayLike | None) -> None:
        if fog_blob_overlay is None:
            return

        fogged_tiles: List[FogTileLike] = []
        for tile_tag, tile in self._tile_by_tag.items():
            state = self._tile_state_by_tag.get(tile_tag)
            if state is not None and self._is_fogged_state(state):
                fogged_tiles.append(tile)

        fog_blob_overlay.sync_fogged_tiles(fogged_tiles)

    def _sync_units(self, player: "Player", units: Iterable[FogUnitLike]) -> None:
        visible_tile_tags = self._get_direct_visible_tile_tags(player)

        for unit in units:
            unit_tile_tag = self._tile_tag(unit.get_tile())
            next_visible = unit_tile_tag in visible_tile_tags
            unit_key = self._unit_key(unit)

            if self._unit_visibility_by_key.get(unit_key) == next_visible:
                continue

            self._unit_visibility_by_key[unit_key] = next_visible
            unit.set_render_visibility(next_visible)

    def _sync_label_overlay(
        self,
        player: "Player",
        *,
        total_tiles: int,
        label_overlay: FogLabelOverlayLike | None,
    ) -> None:
        if label_overlay is None:
            return

        if len(player.vision.get_explored_tile_tags()) == total_tiles:
            label_overlay.root.show()
            return

        label_overlay.root.hide()

    def _resolve_fog_ceiling_z(self, tiles: Iterable[FogTileLike], tile_grid: FogTileGridLike | None) -> float:
        if tile_grid is not None:
            return float(tile_grid.get_max_world_z()) + 0.1

        return max((float(getattr(tile, "pos_z", 0.0)) for tile in tiles), default=0.0) + 0.1

    def _get_direct_visible_tile_tags(self, player: "Player") -> Set[str]:
        get_direct_visible_tile_tags = getattr(player.vision, "get_direct_visible_tile_tags", None)
        if callable(get_direct_visible_tile_tags):
            return set(get_direct_visible_tile_tags())

        get_reveal_tile_tags = getattr(player.vision, "get_reveal_tile_tags", None)
        if callable(get_reveal_tile_tags):
            reveal_tile_tags = set(get_reveal_tile_tags())
            if reveal_tile_tags:
                return reveal_tile_tags

        return set(player.vision.get_visible_tile_tags())

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
        player_tag = getattr(player, "tag", None)
        if isinstance(player_tag, str) and player_tag != "":
            return player_tag

        get_tag = getattr(player, "get_tag", None)
        if callable(get_tag):
            resolved_tag = get_tag()
            if isinstance(resolved_tag, str) and resolved_tag != "":
                return resolved_tag

        return str(id(player))

    def _unit_key(self, unit: FogUnitLike) -> str:
        get_tag = getattr(unit, "get_tag", None)
        if callable(get_tag):
            resolved_tag = get_tag()
            if isinstance(resolved_tag, str) and resolved_tag != "":
                return resolved_tag

        unit_tag = getattr(unit, "tag", None)
        if isinstance(unit_tag, str) and unit_tag != "":
            return unit_tag

        return str(id(unit))

    def _tile_tag(self, tile: FogTileLike) -> str:
        get_tag = getattr(tile, "get_tag", None)
        if callable(get_tag):
            resolved_tag = get_tag()
            if isinstance(resolved_tag, str):
                return resolved_tag

        tile_tag = getattr(tile, "tag", None)
        if isinstance(tile_tag, str):
            return tile_tag

        return ""
