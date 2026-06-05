from typing import Any, Dict, Iterable, List, Protocol, Set, Tuple, TYPE_CHECKING, cast

from gameplay.vision import VisionTileState, is_visible_for_render

if TYPE_CHECKING:
    from gameplay.player import Player


FOGGED_TILE_TINT: Tuple[float, float, float, float] = (0.34, 0.34, 0.40, 1.0)
UNSEEN_TILE_TINT: Tuple[float, float, float, float] = (0.10, 0.10, 0.13, 1.0)


class FogUnitLike(Protocol):
    def get_tile(self) -> "FogTileLike": ...

    def set_render_visibility(self, visible: bool) -> None: ...


class FogTileLike(Protocol):
    tag: str
    renderer: Any

    def get_tag(self) -> str: ...

    def get_units(self) -> Iterable[Any]: ...

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
                force=player_key not in self._synced_player_keys,
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

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
            ):
                touched_grid = True

        if tile_grid is not None and touched_grid:
            tile_grid.collect()

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
            tile_units: Iterable[Any] = tile.get_units()

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
        force: bool = False,
    ) -> bool:
        tile_tag = self._tile_tag(tile)

        if not force and self._tile_state_by_tag.get(tile_tag) is state:
            return False

        self._tile_state_by_tag[tile_tag] = state

        if tile_grid is not None:
            if is_visible_for_render(state):
                tile_grid.show_tile(tile)
            else:
                tile_grid.hide_tile(tile)

            tile_grid.clear_tile_tint(tile)

        tile.renderer.set_fog_ceiling_z(fog_ceiling_z)
        tile.renderer.set_visibility_state(state)

        if is_visible_for_render(state):
            tile_overlay.show_tile(tile)
        else:
            tile_overlay.hide_tile(tile)

        return True

    def _sync_units(self, player: "Player", units: Iterable[FogUnitLike]) -> None:
        for unit in units:
            unit_tile_tag = self._tile_tag(unit.get_tile())
            next_visible = player.vision.get_tile_state(unit_tile_tag) is VisionTileState.VISIBLE
            unit_key = self._unit_key(unit)

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
