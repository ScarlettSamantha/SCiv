from typing import Any, List, Optional, TYPE_CHECKING, Type

from gameplay.civilization import Civilization
from gameplay.civilizations.rome import Rome


if TYPE_CHECKING:
    from system.generators.base import BaseGenerator


class GameSettings:
    def __init__(
        self,
        width: int,
        height: int,
        num_enemies: int,
        generator: Type["BaseGenerator"],
        player: Type[Civilization] = Rome,
        victory_conditions: Optional[List[Any]] = None,
        enemies: Optional[List[Any]] = None,
        difficulty: int = 0,
    ):
        from system.generators.random import RandomGenerator

        self.width: int = width
        self.height: int = height
        self.player: Type[Civilization] = player
        self.enemies: Optional[List[Any]] = enemies
        self.generator: Type["BaseGenerator"] = RandomGenerator
        self.difficulty: int = difficulty
        self.num_enemies: int = num_enemies
