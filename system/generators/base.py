from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type


from gameplay.civic import CivicTree
from gameplay.civics.core.tree.core import CoreCivicTree
from gameplay.civilization import Civilization
from gameplay.leader import Leader
from gameplay.personality import Personality

from gameplay.repositories.civilization import Civilization as CivilizationRepository
from gameplay.repositories.personality import (
    PersonalityRepository as PersonalityRepository,
)

from gameplay.tech import TechTree
from gameplay.techs.trees.core import Core

from managers.i18n import T_TranslationOrStrOrNone, get_i18n, t_
from managers.player import PlayerManager
from system.game_settings import GameSettings

if TYPE_CHECKING:
    from main import SCIV
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.player import Player


class WorldParams:
    (
        arctic,  # id 1 | 'a' | 'Arctic'
        tundra,  # id 2 | 'u' | 'Tundra'
        alpine_tundra,  # id 3 | 'p' | 'Alpine Tundra'
        desert,  # id 4 | 'd' | 'Desert'
        scrubland,  # id 5 | 's' | 'Scrubland'
        savanna,  # id 6 | 'S' | 'Savanna'
        grasslands,  # id 7 | 'g' | 'Grasslands'
        boreal_forest,  # id 8 | 'b' | 'Boreal Forest'
        temperate_forest,  # id 9 | 't' | 'Temperate Forest'
        temperate_rainforest,  # id 10 | 'T' | 'Temperate Rainforest'
        tropical_forest,  # id 11 | 'r' | 'Tropical Forest'
        tropical_rainforest,  # id 12 | 'R' | 'Tropical Rainforest'
    ) = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    desert_temperature_threshold = 20
    grass_temperature_upper_threshold = 30
    grass_temperature_lower_threshold = 10
    forest_lower_threshold = 2
    moisture_threshold_mangrove_jungle = 12
    moisture_threshold_heavy_forest = 8
    light_jungle_temperature_threshold = 25
    cold_forrest_temperature_threshold = 8
    schrubland_temperature_threshold = 4
    flat_to_hills_threshold = 175
    hills_to_mountains_threshold = 217


class BaseGenerator(ABC):
    NAME = t_("generic.unimplemented")
    DESCRIPTION = t_("generic.unimplemented")

    def __init__(self, config: GameSettings, base: "SCIV") -> None:
        from managers.world import World

        self.config: GameSettings = config
        self.base: "SCIV" = base
        self.world: World = World.get_singleton_instance()
        self.world_generation_stats: Dict[str, Any] = {}

    @abstractmethod
    def generate(self) -> bool: ...

    def generate_player(
        self,
        personality: Personality,
        civilization: Civilization,
        name: T_TranslationOrStrOrNone = None,
        turn_order: int = 0,
        leader: Optional[Leader] = None,
        is_player: bool = False,
        tech_tree: Type[TechTree] = Core,
        civic_tree: Type[CivicTree] = CoreCivicTree,
        is_nature: bool = False,
        is_barbarian: bool = False,
    ) -> "Player":
        from gameplay.player import Player

        if leader is None:
            leader = civilization.random_leader()

        if name is None:
            civ_name: str = str(civilization.name)
            leader_name: str = str(leader.name)

            _name: str = f"{civ_name} - {leader_name}"
        else:
            _name: str = get_i18n().lookup(name)

        player: Player = Player(_name, turn_order, personality, civilization, leader)

        player.is_human = is_player
        player.is_nature = is_nature
        player.is_barbarian = is_barbarian

        player.tech.set_tech_tree(tech_tree())
        player.civics.set_tree(civic_tree())

        self.assign_ai(player)
        if player.is_registered is False:
            player.register()

        return player

    def assign_ai(self, player: "Player") -> None:
        """
        Assigns an AI class to a player
        """
        from gameplay.ai.implementations.barbarians import BarbariansAI
        from gameplay.ai.implementations.enemy import EnemyAI
        from gameplay.ai.implementations.nature import NatureAI
        from gameplay.ai.implementations.player import PlayerAI

        if player.is_human:
            ai = PlayerAI(player)
        elif player.is_nature:
            ai = NatureAI(player)
        elif player.is_barbarian:
            ai = BarbariansAI(player)
        else:
            ai = EnemyAI(player)

        player.set_ai(ai)

    def setup_players(self, player_civilization: Type[Civilization]) -> List["Player"] | None:
        players: List[Player] = []
        civs_ingame: List[Type[Civilization]] = []

        for i in range(self.config.num_enemies + 3):  # +1 for the player
            if i == 0:  # Player
                chosen_civilization: Type[Civilization] = player_civilization
                civs_ingame.append(chosen_civilization)
            elif i == 1:  # Nature
                chosen_civilization: Type[Civilization] = CivilizationRepository.get("nature")  # type: ignore
                civs_ingame.append(chosen_civilization)
            elif i == 2:  # Barbarians
                chosen_civilization: Type[Civilization] = CivilizationRepository.get("barbarians")
                civs_ingame.append(chosen_civilization)
            else:  # AI
                chosen_civilization: Type[Civilization] = CivilizationRepository.random(exclude=True)  # type: ignore #due to the num argument is 1 it will always return a single instance not a list of instances.
                while True:
                    chosen_civilization = CivilizationRepository.random(exclude=True)  # type: ignore #due to the num argument is 1 it will always return a single instance not a list of instances.
                    already_ingame: bool = False

                    if chosen_civilization in civs_ingame:
                        already_ingame = True
                    else:
                        civs_ingame.append(chosen_civilization)

                    if already_ingame is False:  # We try to avoid having the same civilization twice
                        break

            chosen_personality: Type[Personality] = PersonalityRepository.random()  # type: ignore # due to the num argument is 1 it will always return a single instance not a list of instances.

            if isinstance(chosen_civilization, list):
                raise AssertionError(
                    "CivilizationRepository.random() returned a list it should be one. as parameter is 1"
                )

            if isinstance(chosen_personality, list):
                raise AssertionError(
                    "PersonalityRepository.random() returned a list it should be one. as parameter is 1"
                )

            if isinstance(chosen_civilization, Type):  # type: ignore
                civ = chosen_civilization()
            else:
                civ = CivilizationRepository.get(chosen_civilization)()

            player: Player = self.generate_player(
                personality=chosen_personality(),
                civilization=civ,
                leader=None,  # None means it will pick from its own list of registered leaders
                turn_order=i,
                is_player=i == 0,
                is_nature=i == 1,
                is_barbarian=i == 2,
            )
            player.id = str(i)

            players.append(player)

            if player.is_human:
                PlayerManager.add(player, True)
            elif player.is_nature:
                PlayerManager.set_nature(player)
            elif player.is_barbarian:
                PlayerManager.set_barbarian(player)
            else:
                PlayerManager.add(player, False)

        return players

    def place_starting_units(
        self,
        max_attempts: int = 50,
        land_ratio_threshold: float = 0.6,
        land_check_radius: int = 4,
        map_edge_buffer: int = 3,
    ) -> bool:
        from gameplay.units.core.classes.civilian.settler import Settler
        from gameplay.repositories.tile import TileRepository

        units: List["Settler"] = []
        occupied_tiles: List["BaseTile"] = []  # Track placed player locations

        min_distances: List[int] = [5, 4, 3]  # Distances to attempt

        def has_sufficient_land(tile: "BaseTile", radius: int, threshold: float) -> bool:
            """Checks if the tile has at least the given ratio of land within the radius."""
            neighbors: List[BaseTile] = TileRepository.get_neighbors(tile, radius=radius)
            land_tiles = sum(1 for n in neighbors if not n.is_water)
            return (land_tiles / max(1, len(neighbors))) >= threshold

        for player in PlayerManager.players().values():
            if player.is_nature or player.is_barbarian:  # Skip nature and barbarian players as they don't have settlers
                continue

            spawn_tile: Optional[BaseTile] = None
            fallback_tile: Optional[BaseTile] = None  # Store a fallback tile if needed

            for min_distance in min_distances:
                for _ in range(max_attempts):  # Limit attempts to prevent infinite loops
                    _spawn_tile: Optional[BaseTile] = self.base.world.random_tile()

                    if not _spawn_tile or not _spawn_tile.is_spawnable_upon() or not _spawn_tile.is_passable():
                        continue

                    distance_ok = all(
                        TileRepository.hex_distance(_spawn_tile, tile) >= min_distance for tile in occupied_tiles
                    )

                    # Check if the tile has coastal neighbors
                    neighbors: List[BaseTile] = TileRepository.get_neighbors(_spawn_tile, radius=1)
                    has_coastal_neighbor: bool = any(n.is_water and n.is_coast for n in neighbors)
                    near_map_edge: bool = TileRepository.is_near_map_edge(
                        self.base.world.get_size(), _spawn_tile, map_edge_buffer
                    )
                    sufficient_land: bool = has_sufficient_land(_spawn_tile, land_check_radius, land_ratio_threshold)

                    # Prefer coastal-adjacent tiles that are not near the map edge and have sufficient land
                    if has_coastal_neighbor and not near_map_edge and sufficient_land and distance_ok:
                        spawn_tile = _spawn_tile
                        break  # Stop looking if we find a valid tile

                    # Store a fallback tile that avoids map edges and has enough land if possible
                    if distance_ok and not near_map_edge and sufficient_land and fallback_tile is None:
                        fallback_tile = _spawn_tile  # Store the first valid inland tile

                    # Secondary fallback: Accept a tile near the edge if necessary
                    if distance_ok and fallback_tile is None:
                        fallback_tile = _spawn_tile

                if spawn_tile:
                    break  # Stop lowering distance if we found a good tile

            # Fallback if no preferred tile was found
            if spawn_tile is None:
                spawn_tile = fallback_tile

            if spawn_tile is None:
                raise Exception("No suitable spawn location found for a player")

            unit: Settler = Settler(spawn_tile)
            unit.owner = player
            units.append(unit)
            occupied_tiles.append(spawn_tile)
            unit.spawn_on(spawn_tile, player)

        return len(units) > 0
