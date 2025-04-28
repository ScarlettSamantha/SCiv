import random
from typing import TYPE_CHECKING, List

from gameplay.ai.core import AI
from gameplay.ai.goal import Goals
from gameplay.repositories.tile import TileRepository
from gameplay.tiles.base_tile import BaseTile
from gameplay.units.core.classes.military.barbarian_lion import BarbarianLion
from managers.turn import Turn

if TYPE_CHECKING:
    from gameplay.player import Player


class NatureAI(AI):
    """
    NatureAI is a subclass of AI that represents the AI that controls the nature of the game.
    It manages nature events and the world over time.
    """

    def __init__(self, player: "Player"):
        super().__init__(player)
        # cache of passable, non-city, neighbor-empty tiles for spawning threats
        self._spawn_tiles_cache: List["BaseTile"] = []
        self._spawn_cache_from_turn: int = 0

    def register_end_goal(self) -> Goals:
        return Goals()

    def register_goals(self) -> Goals:
        return Goals()

    def on_turn_end(self) -> None: ...

    def on_turn_start(self) -> None: ...

    def on_game_end(self) -> None: ...

    def on_game_start(self) -> None:
        # build cache once at game start
        self._build_spawn_tile_cache()
        self._spawn_initial_threat()

    def _build_spawn_tile_cache(self) -> None:
        """Populate the cache with all valid tiles for threat spawning."""
        all_land = TileRepository.search_passable_land()
        valid_tiles: List["BaseTile"] = []
        for tile in all_land:
            if tile.is_city():
                continue

            neighbors = TileRepository.get_neighbors(tile, 2, False, False)
            if any(neigh.is_city() or neigh.units for neigh in neighbors):
                continue

            valid_tiles.append(tile)

        self._spawn_tiles_cache = valid_tiles
        self._spawn_cache_from_turn = Turn.get_singleton_instance().get_turn()

    def _spawn_initial_threat(self) -> None:
        """
        Spawn one BarbarianLion for every 120 cached tiles,
        sampling without replacement to avoid duplicates.
        """
        if not self._spawn_tiles_cache:
            return

        if (count := len(self._spawn_tiles_cache) // 30) <= 0:
            return

        tiles_to_spawn = random.sample(self._spawn_tiles_cache, k=count)
        for tile in tiles_to_spawn:
            self.spawn_unit(BarbarianLion, tile)
