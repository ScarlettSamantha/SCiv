import datetime
import random
from typing import TYPE_CHECKING, List

from gameplay.ai.core import AI
from gameplay.ai.goal import Goals
from gameplay.ai.goals.eliminate_player import EliminatePlayer
from gameplay.repositories.tile import TileRepository
from gameplay.tile import Tile
from gameplay.units.core.classes.military.barbarian_lion import BarbarianLion
from helpers.debug import Debug
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
        self._spawn_tiles_cache: List["Tile"] = []
        self._spawn_cache_from_turn: int = 0
        self.logger = self.player.logger.getChild("nature_ai")
        self.should_log: bool = Debug.system_ai()

    def register_end_goal(self) -> Goals:
        return Goals()

    def register_goals(self) -> Goals:
        return Goals()

    def calculate_goals(self) -> None:
        if not self.has_goal():
            for player in self.get_players().values():
                if self.should_log:
                    self.logger.debug(f"Adding goal to eliminate player {player.name}")
                self.add_goal(EliminatePlayer(self, player))

        if self.has_goal():
            for goal in self.get_goals():
                if self.should_log:
                    self.logger.debug(f"Checking goal {goal.name} for completion")
                if goal.is_achieved():
                    if self.should_log:
                        self.logger.debug(f"Goal {goal.name} is achieved, removing it")
                    self.remove_goal(goal)
                else:
                    if self.should_log:
                        self.logger.debug(f"Goal {goal.name} is not achieved, keeping it")

        for unit in self.get_units():
            if self.goals.has_goal_for_unit(unit):
                if self.should_log:
                    self.logger.debug(f"Unit {unit.name} already has a goal, skipping")
                continue

            if (goal := self.create_goals_for_unit(unit)) is not None:
                if self.should_log:
                    self.logger.debug(f"Creating goal for unit {unit.name}: {goal.name}")
                self.add_goal(goal)
            else:
                if self.should_log:
                    self.logger.debug(f"No goal for {unit.name}, wandering")
                self.on_wander(unit)

    def on_turn_end(self) -> None:
        start_time = datetime.datetime.now()
        if self.should_log:
            self.logger.debug("NatureAI on_turn_end")
        # check if we need to rebuild the spawn tile cache
        if self._spawn_cache_from_turn != Turn.get_singleton_instance().get_turn():
            self._build_spawn_tile_cache()
        if self.should_log:
            self.logger.debug(
                "Took %d seconds to build spawn tile cache", (datetime.datetime.now() - start_time).total_seconds()
            )
        self.calculate_goals()

        if self.should_log:
            self.logger.debug(
                "Took %d seconds to calculate goals", (datetime.datetime.now() - start_time).total_seconds()
            )

        if self.has_goal():
            for goal in self.get_goals():
                if not goal.is_for_unit():
                    continue
                if goal.needs_turn_processing:
                    goal.turn_tick()
                if goal.is_achieved():
                    self.remove_goal(goal)
            if self.should_log:
                self.logger.debug(
                    "Took %d seconds to tick goals", (datetime.datetime.now() - start_time).total_seconds()
                )
        if self.should_log:
            self.logger.debug(
                "AI took %d seconds to process turn", (datetime.datetime.now() - start_time).total_seconds()
            )

    def on_turn_start(self) -> None: ...

    def on_game_end(self) -> None: ...

    def on_game_start(self) -> None:
        # build cache once at game start
        self._build_spawn_tile_cache()
        self._spawn_initial_threat()

    def _build_spawn_tile_cache(self) -> None:
        """
        Efficiently populate the cache with all valid tiles for threat spawning.
        A valid tile:
        - Is passable land
        - Is not a city
        - Itself and all tiles within radius-2 have no cities/units
        """
        all_land: List["Tile"] = TileRepository.search_passable_land()
        # Index all city and unit tiles for O(1) lookup
        city_tiles = {tile for tile in all_land if tile.is_city()}
        unit_tiles = {tile for tile in all_land if tile.units.has_any()}
        # If cities/units can be on non-passable land, you may need to expand this

        valid_tiles: List["Tile"] = []

        for tile in all_land:
            # Skip if tile itself is city or has units
            if tile in city_tiles or tile in unit_tiles:
                continue

            # Get radius-2 neighbors
            neighbors = TileRepository.get_neighbors(tile, 2, False, False)
            # Check if any neighbor is a city or has units (set lookup is fast)
            if any(neigh in city_tiles or neigh in unit_tiles for neigh in neighbors):
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
