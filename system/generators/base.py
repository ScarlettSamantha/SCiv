from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

from data.tiles.base_tile import BaseTile
from gameplay.civilization import Civilization
from gameplay.leader import Leader
from gameplay.personality import Personality
from gameplay.player import Player
from gameplay.repositories.civilization import Civilization as CivilizationRepository
from gameplay.repositories.personality import (
    PersonalityRepository as PersonalityRepository,
)
from gameplay.units.unit_base import UnitBaseClass
from managers.i18n import T_TranslationOrStrOrNone, get_i18n, _t
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

        return player

    def setup_players(self, player_civilization: Type[Civilization]) -> List[Player] | None:
        if self.config.num_enemies is None:
            raise ValueError("Number of enemies not set")

        players = []

        for i in range(self.config.num_enemies + 1):  # +1 for the player
            if i == 0:
                chosen_civilization: Type[Civilization] = player_civilization
            else:
                chosen_civilization: Type[Civilization] = CivilizationRepository.random()  # type: ignore # type: ignore, due to the num argument is 1 it will always return a single instance not a list of instances.
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

            players.append(player)
            PlayerManager.add(player, i == 0)
        return players

    def place_starting_units(self) -> bool:
        from gameplay.units.core.classes.civilian.settler import Settler

        unit_manager: Unit = Unit.get_instance()
        units: List[UnitBaseClass] = []
        for player in PlayerManager.players().values():
            unit: Settler = Settler(base=self.base)
            unit.owner = player
            spawn_tile: Optional[BaseTile] = None
            # We need to find a tile to spawn the unit on
            while True:
                _spawn_tile: Optional[BaseTile] = self.base.world.random_tile()

                if _spawn_tile is None:
                    raise Exception("No tiles found to spawn unit on")

                if _spawn_tile.is_spawnable_upon() is False:
                    continue

                spawn_tile = _spawn_tile
                break

            units.append(unit)
            spawn_tile.add_unit(unit)

            # Spawn first otherwise the unit will not have a tag
            unit.spawn()

            player.units.add_unit(unit)
            unit_manager.add_unit(unit)

        return len(units) > 0
