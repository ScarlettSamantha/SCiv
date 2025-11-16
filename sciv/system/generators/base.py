from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from gameplay.civic import CivicTree
from gameplay.civics.core.tree.core import CoreCivicTree
from gameplay.civilization import Civilization
from gameplay.leader import Leader
from gameplay.personalities.base import BasePersonality
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
    from game import OpenCiv
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from system.tile_grid import TileModelGrid


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
        wasteland,  # id 13 | 'w' | 'Wasteland'
    ) = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)

    desert_temperature_threshold = 17
    grass_temperature_upper_threshold = 30
    grass_temperature_lower_threshold = 10
    forest_lower_threshold = 5.0
    moisture_threshold_mangrove_jungle = 16
    moisture_threshold_heavy_forest = 10
    moisture_threshold_tundra_snow_lower = 2
    moisture_threshold_grassland_lower = 4
    light_jungle_temperature_threshold = 30
    cold_forrest_temperature_threshold = 8
    scrubland_temperature_threshold = 4
    flat_to_hills_threshold = 170
    hills_to_mountains_threshold = 217


class BaseGenerator(ABC):
    NAME = t_("generic.unimplemented")
    DESCRIPTION = t_("generic.unimplemented")

    def __init__(self, config: GameSettings, base: "OpenCiv") -> None:
        from managers.world import World

        self.config: GameSettings = config
        self.base: "OpenCiv" = base
        self.world: World = World.get_singleton_instance()
        self.world_generation_stats: Dict[str, Any] = {}
        self.model_grid: Optional[TileModelGrid] = None
        self.debug_dump_data: Dict[str, Dict[str, Any]] = {
            "meta": {
                "rows": self.config.width,
                "cols": self.config.height,
                "seed": self.config.seed,
                "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "tiles": {},
        }
        self.grid: Dict[Tuple[int, int], "Tile"] = {}

    @abstractmethod
    def generate(self) -> bool: ...

    def generate_player(
        self,
        personality: BasePersonality,
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
        players: List["Player"] = []
        civs_ingame: List[Type[Civilization]] = []

        start_config: Any = getattr(self.config, "start_config", None)
        raw_players: Any = start_config.get("players") if isinstance(start_config, Dict) else None  # type: ignore
        config_players: List[Dict[str, Any]] = raw_players if isinstance(raw_players, list) else []  # type: ignore

        if config_players:
            human_entries: List[Dict[str, Any]] = [p for p in config_players if bool(p.get("is_human"))]
            local_entry: Dict[str, Any] = human_entries[0] if human_entries else config_players[0]

            self.config.num_enemies = max(0, len(config_players) - 1)

            ordered_entries: List[Tuple[Optional[Dict[str, Any]], bool, bool, bool]] = []

            ordered_entries.append((local_entry, True, False, False))

            nature_civ_cls: Type[Civilization] = CivilizationRepository.get("nature")  # type: ignore
            barb_civ_cls: Type[Civilization] = CivilizationRepository.get("barbarians")

            ordered_entries.append(({"civilization": nature_civ_cls, "leader": None}, False, True, False))
            ordered_entries.append(({"civilization": barb_civ_cls, "leader": None}, False, False, True))

            remaining_entries: List[Dict[str, Any]] = [p for p in config_players if p is not local_entry]
            for entry in remaining_entries:
                ordered_entries.append((entry, False, False, False))

            for i, (entry, is_player, is_nature, is_barbarian) in enumerate(ordered_entries):
                civ_cls: Optional[Type[Civilization]] = None
                leader_cls: Optional[Type[Leader]] = None

                if entry is not None:
                    civ_val: Any = entry.get("civilization")
                    if isinstance(civ_val, type) and issubclass(civ_val, Civilization):
                        civ_cls = civ_val
                    elif isinstance(civ_val, str):
                        civ_cls = CivilizationRepository.get(civ_val)  # type: ignore

                    leader_val: Any = entry.get("leader")
                    if leader_val is not None and isinstance(leader_val, type) and issubclass(leader_val, Leader):
                        leader_cls = leader_val

                if civ_cls is None:
                    if is_player:
                        civ_cls = player_civilization
                    else:
                        while True:
                            candidate: Type[Civilization] = CivilizationRepository.random(exclude=True)  # type: ignore
                            assert issubclass(candidate, Civilization), (
                                "CivilizationRepository.random() returned an instance it should be a class."
                            )
                            if candidate not in civs_ingame:
                                civ_cls = candidate
                                break

                civs_ingame.append(civ_cls)  # type: ignore[arg-type]

                chosen_personality: Type[BasePersonality] = PersonalityRepository.random()  # type: ignore
                if isinstance(chosen_personality, list):
                    raise AssertionError(
                        "PersonalityRepository.random() returned a list it should be one. as parameter is 1"
                    )

                civ = civ_cls()  # type: ignore[call-arg]
                leader: Optional[Leader] = leader_cls() if leader_cls is not None else None

                player: "Player" = self.generate_player(
                    personality=chosen_personality(),
                    civilization=civ,
                    leader=leader,
                    turn_order=i,
                    is_player=is_player,
                    is_nature=is_nature,
                    is_barbarian=is_barbarian,
                )
                player.id = str(i)

                players.append(player)

                player_manager = PlayerManager()
                player_manager.set_singleton_instance(player_manager)
                if player.turn_order == 0:
                    player_manager.add(player, True)
                elif player.is_nature:
                    player_manager.set_nature(player)
                elif player.is_barbarian:
                    player_manager.set_barbarian(player)
                else:
                    player_manager.add(player, False)

            return players

        players: List["Player"] = []
        civs_ingame = []

        for i in range(self.config.num_enemies + 3):
            if i == 0:
                chosen_civilization: Type[Civilization] = player_civilization
                civs_ingame.append(chosen_civilization)
            elif i == 1:
                chosen_civilization = CivilizationRepository.get("nature")  # type: ignore
                civs_ingame.append(chosen_civilization)
            elif i == 2:
                chosen_civilization = CivilizationRepository.get("barbarians")
                civs_ingame.append(chosen_civilization)
            else:
                chosen_civilization = CivilizationRepository.random(exclude=True)  # type: ignore
                while True:
                    chosen_civilization = CivilizationRepository.random(exclude=True)  # type: ignore
                    assert issubclass(chosen_civilization, Civilization), (
                        "CivilizationRepository.random() returned an instance it should be a class."
                    )
                    already_ingame: bool = False

                    if chosen_civilization in civs_ingame:
                        already_ingame = True
                    else:
                        civs_ingame.append(chosen_civilization)

                    if already_ingame is False:
                        break

            chosen_personality: Type[BasePersonality] = PersonalityRepository.random()  # type: ignore

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

            player: "Player" = self.generate_player(
                personality=chosen_personality(),
                civilization=civ,
                leader=None,
                turn_order=i,
                is_player=i == 0,
                is_nature=i == 1,
                is_barbarian=i == 2,
            )
            player.id = str(i)

            players.append(player)

            player_manager = PlayerManager()
            player_manager.set_singleton_instance(player_manager)
            if player.turn_order == 0:
                player_manager.add(player, True)
            elif player.is_nature:
                player_manager.set_nature(player)
            elif player.is_barbarian:
                player_manager.set_barbarian(player)
            else:
                player_manager.add(player, False)

        return players

    def place_starting_units(
        self,
        max_attempts: int = 50,
        land_ratio_threshold: float = 0.6,
        land_check_radius: int = 4,
        map_edge_buffer: int = 3,
    ) -> bool:
        from gameplay.repositories.tile import TileRepository
        from gameplay.units.core.classes.civilian.settler import Settler

        units: List[Unit] = []
        occupied_tiles: List["Tile"] = []

        min_distances: List[int] = [5, 4, 3]

        def has_sufficient_land(tile: "Tile", radius: int, threshold: float) -> bool:
            neighbors: List[Tile] = TileRepository.get_neighbors(tile, radius=radius)
            land_tiles = sum(1 for n in neighbors if not n.is_water)
            return (land_tiles / max(1, len(neighbors))) >= threshold

        for player in PlayerManager.players().values():
            if player.is_nature or player.is_barbarian:
                continue

            spawn_tile: Optional[Tile] = None
            fallback_tile: Optional[Tile] = None

            for min_distance in min_distances:
                for _ in range(max_attempts):
                    _spawn_tile: Optional[Tile] = self.base.world.random_tile()

                    if not _spawn_tile or not _spawn_tile.is_spawnable_upon() or not _spawn_tile.is_passable():
                        continue

                    distance_ok = all(
                        TileRepository.hex_distance(_spawn_tile, tile) >= min_distance for tile in occupied_tiles
                    )

                    neighbors: List[Tile] = TileRepository.get_neighbors(_spawn_tile, radius=1)
                    has_coastal_neighbor: bool = any(n.is_water and n.is_coast for n in neighbors)
                    near_map_edge: bool = TileRepository.is_near_map_edge(
                        self.base.world.get_size(), _spawn_tile, map_edge_buffer
                    )
                    sufficient_land: bool = has_sufficient_land(_spawn_tile, land_check_radius, land_ratio_threshold)

                    if has_coastal_neighbor and not near_map_edge and sufficient_land and distance_ok:
                        spawn_tile = _spawn_tile
                        break

                    if distance_ok and not near_map_edge and sufficient_land and fallback_tile is None:
                        fallback_tile = _spawn_tile

                    if distance_ok and fallback_tile is None:
                        fallback_tile = _spawn_tile

                if spawn_tile:
                    break

            if spawn_tile is None:
                spawn_tile = fallback_tile

            if spawn_tile is None:
                raise Exception("No suitable spawn location found for a player")

            occupied_tiles.append(spawn_tile)
            unit = Settler.spawn_on(spawn_tile, player)
            units.append(unit)  # type: ignore[union-attr]

            companion_spawn_tile: Optional[Tile] = None
            _neighbors: List[Tile] = TileRepository.get_neighbors(spawn_tile, radius=1)
            for neighbor in _neighbors:
                if neighbor.is_spawnable_upon():
                    companion_spawn_tile = neighbor
                    break

            if companion_spawn_tile:
                from gameplay.units.core.classes.military.club_man import ClubMan

                companion_unit = ClubMan.spawn_on(companion_spawn_tile, player)
                units.append(companion_unit)

        return len(units) > 0

    @abstractmethod
    def randomize_seed(self) -> int:
        import random

        seed = random.randint(0, 2**31 - 1)
        self.config.seed = seed
        self.debug_dump_data["meta"]["seed"] = seed
        return seed
