from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

from gameplay.civilization import Civilization
from gameplay.leader import Leader
from gameplay.personality import Personality
from gameplay.player import Player
from gameplay.repositories.civilization import Civilization as CivilizationRepository
from gameplay.repositories.personality import (
    PersonalityRepository as PersonalityRepository,
)
from gameplay.repositories.tile import TileRepository
from gameplay.tiles.base_tile import BaseTile
from helpers.tiles import TileHelper
from managers.i18n import T_TranslationOrStrOrNone, _t, get_i18n
from managers.player import PlayerManager
from managers.unit import Unit
from system.game_settings import GameSettings


class BaseGenerator(ABC):
    NAME = _t("generic.unimplemented")
    DESCRIPTION = _t("generic.unimplemented")

    def __init__(self, config: GameSettings, base: Any) -> None:
        from managers.world import World

        self.config: GameSettings = config
        self.base: Any = base
        self.world: World = World.get_instance()

    @abstractmethod
    def generate(self) -> bool:
        pass

    def generate_player(
        self,
        personality: Personality,
        civilization: Civilization,
        name: T_TranslationOrStrOrNone = None,
        turn_order: int = 0,
        leader: Optional[Leader] = None,
    ):
        if leader is None:
            leader = civilization.random_leader()

        if name is None:
            civ_name: str = str(civilization.name)
            leader_name: str = str(leader.name)

            _name: str = f"{civ_name} - {leader_name}"
        else:
            _name: str = get_i18n().lookup(name)

        player = Player(_name, turn_order, personality, civilization, leader)
        if player.is_registered is False:
            player.register()

        return player

    def setup_players(self, player_civilization: Type[Civilization]) -> List[Player] | None:
        if self.config.num_enemies is None:
            raise ValueError("Number of enemies not set")

        players = []
        civs_ingame = []

        for i in range(self.config.num_enemies + 1):  # +1 for the player
            if i == 0:  # Player
                chosen_civilization: Type[Civilization] = player_civilization
                civs_ingame.append(chosen_civilization)
            else:  # AI
                chosen_civilization: Type[Civilization] = CivilizationRepository.random()  # type: ignore # type: ignore, due to the num argument is 1 it will always return a single instance not a list of instances.
                while True:
                    chosen_civilization = CivilizationRepository.random()  # type: ignore # type: ignore, due to the num argument is 1 it will always return a single instance not a list of instances.
                    already_ingame = False

                    if chosen_civilization in civs_ingame:
                        already_ingame = True
                    else:
                        civs_ingame.append(chosen_civilization)

                    if already_ingame is False:  # We try to avoid having the same civilization twice
                        break

            chosen_personality: Type[Personality] = PersonalityRepository.random()  # type: ignore # type: ignore, due to the num argument is 1 it will always return a single instance not a list of instances.

            if isinstance(chosen_civilization, list):
                raise AssertionError(
                    "CivilizationRepository.random() returned a list it should be one. as parameter is 1"
                )

            if isinstance(chosen_personality, list):
                raise AssertionError(
                    "PersonalityRepository.random() returned a list it should be one. as parameter is 1"
                )

            if isinstance(chosen_civilization, Type):
                civ = chosen_civilization()
            else:
                civ = CivilizationRepository.get(chosen_civilization)()

            player = self.generate_player(
                personality=chosen_personality(),
                civilization=civ,
                leader=None,  # None means it will pick from its own list of registered leaders
                turn_order=i,
            )
            player.id = str(i)

            players.append(player)
            PlayerManager.add(player, i == 0)
        return players

    def place_starting_units(self, max_attempts: int = 50) -> bool:
        from gameplay.units.core.classes.civilian.settler import Settler

        unit_manager: Unit = Unit.get_instance()
        units: List["Settler"] = []
        occupied_tiles: List[BaseTile] = []  # Track placed player locations

        min_distances = [5, 4, 3]  # Distances to attempt

        for player in PlayerManager.players().values():
            unit = Settler(base=self.base)
            unit.owner = player
            spawn_tile: Optional[BaseTile] = None
            fallback_tile: Optional[BaseTile] = None  # Store a fallback tile if needed

            for min_distance in min_distances:
                for _ in range(max_attempts):  # Limit attempts to prevent infinite loops
                    _spawn_tile: Optional[BaseTile] = self.base.world.random_tile()

                    if not _spawn_tile or not _spawn_tile.is_spawnable_upon() or not _spawn_tile.is_passable():
                        continue

                    distance_ok = all(
                        TileHelper.hex_distance(_spawn_tile, tile) >= min_distance for tile in occupied_tiles
                    )

                    # **Check if any of the tile's neighbors are coastal**
                    neighbors = TileRepository.get_neighbors(_spawn_tile, radius=1)
                    has_coastal_neighbor = any(n.is_water and n.is_coast for n in neighbors)

                    # **Prioritize tiles with coastal neighbors**
                    if has_coastal_neighbor and distance_ok:
                        spawn_tile = _spawn_tile
                        break  # Stop looking if we find a valid tile near the coast

                    # **Store a fallback tile if we don't find a coastal-adjacent one**
                    if distance_ok and fallback_tile is None:
                        fallback_tile = _spawn_tile  # Store the first valid non-coastal-adjacent tile

                if spawn_tile:
                    break  # Stop lowering distance if we found a suitable coastal-adjacent tile

            # **Fallback to the non-coastal-adjacent tile if no valid coastal-adjacent tile was found**
            if spawn_tile is None:
                spawn_tile = fallback_tile

            if spawn_tile is None:
                raise Exception("No suitable spawn location found for a player")

            units.append(unit)
            spawn_tile.add_unit(unit)
            occupied_tiles.append(spawn_tile)  # Track this tile as occupied

            unit.spawn()
            player.units.add_unit(unit)
            unit_manager.add_unit(unit)

        return len(units) > 0
