from collections.abc import Iterable
from typing import Any, Protocol, TYPE_CHECKING

from gameplay.vision import VisionTileState, build_tile_visibility_states, is_visible_for_render

if TYPE_CHECKING:
    from gameplay.player import Player


FOGGED_TILE_TINT: tuple[float, float, float, float] = (0.34, 0.34, 0.40, 1.0)
UNSEEN_TILE_TINT: tuple[float, float, float, float] = (0.10, 0.10, 0.13, 1.0)


class FogTileLike(Protocol):
    tag: str
    renderer: Any

    def get_tag(self) -> str: ...


class FogUnitLike(Protocol):
    def get_tile(self) -> FogTileLike: ...

    def set_render_visibility(self, visible: bool) -> None: ...


class FogTileGridLike(Protocol):
    def hide_tile(self, tile_or_index: Any) -> None: ...

    def show_tile(self, tile_or_index: Any) -> None: ...

    def set_tile_tint(self, tile_or_index: Any, rgba: tuple[float, float, float, float]) -> None: ...

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
        self._synced_player_keys: set[str] = set()

    def reset(self) -> None:
        self._synced_player_keys.clear()

    def apply(
        self,
        player: "Player",
        tiles: Iterable[FogTileLike],
        units: Iterable[FogUnitLike],
        *,
        tile_grid: FogTileGridLike | None,
        tile_overlay: FogTileOverlayLike,
        label_overlay: FogLabelOverlayLike | None = None,
        changed_tile_tags: set[str] | None = None,
    ) -> None:
        cached_tiles = list(tiles)
        candidate_tiles = cached_tiles
        player_key = self._player_key(player)
        fog_ceiling_z = self._resolve_fog_ceiling_z(cached_tiles, tile_grid)

        if changed_tile_tags is not None and player_key in self._synced_player_keys:
            candidate_tiles = [tile for tile in cached_tiles if tile.tag in changed_tile_tags]

        visibility_states = build_tile_visibility_states(player.vision, candidate_tiles)
        for tile in candidate_tiles:
            state = visibility_states.get(tile.tag, VisionTileState.UNSEEN)
            self._apply_tile_state(tile, state, tile_grid=tile_grid, tile_overlay=tile_overlay, fog_ceiling_z=fog_ceiling_z)

        if tile_grid is not None and candidate_tiles:
            tile_grid.collect()

        visible_tile_tags = player.vision.get_visible_tile_tags()
        for unit in units:
            unit.set_render_visibility(unit.get_tile().get_tag() in visible_tile_tags)

        self._sync_label_overlay(player, total_tiles=len(cached_tiles), label_overlay=label_overlay)
        self._synced_player_keys.add(player_key)

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

    def _apply_tile_state(
        self,
        tile: FogTileLike,
        state: VisionTileState,
        *,
        tile_grid: FogTileGridLike | None,
        tile_overlay: FogTileOverlayLike,
        fog_ceiling_z: float,
    ) -> None:
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
            return

        tile_overlay.hide_tile(tile)

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

    def _resolve_fog_ceiling_z(self, tiles: list[FogTileLike], tile_grid: FogTileGridLike | None) -> float:
        if tile_grid is not None:
            return float(tile_grid.get_max_world_z()) + 0.1

        return max((float(getattr(tile, "pos_z", 0.0)) for tile in tiles), default=0.0) + 0.1
