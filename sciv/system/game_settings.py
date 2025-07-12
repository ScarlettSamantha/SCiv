from typing import TYPE_CHECKING, Any, List, Optional, Type

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
        seed: Optional[int] = None,
    ):
        from system.generators.basic import Basic

        self.width: int = width
        self.height: int = height
        self.player: Type[Civilization] = player
        self.enemies: Optional[List[Any]] = enemies
        self.generator: Type["BaseGenerator"] = Basic
        self.difficulty: int = difficulty
        self.num_enemies: int = num_enemies
        self.seed: Optional[int] = seed

    def __getstate__(self) -> object:
        return self.__dict__.copy()

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)

    def dump(self) -> dict[str, Any]:
        data: dict[str, Any] = self.__dict__.copy()
        data["player"] = f"{self.player.__module__}.{self.player.__class__.__name__}"
        return data

    def load_state(self, state: dict[str, Any]) -> None:
        from managers.entity import EntityManager

        self.__dict__.update(state)
        self.player = EntityManager.dynamic_import(self.player)  # type: ignore
