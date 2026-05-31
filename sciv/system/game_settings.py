from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from gameplay.civilization import Civilization
from gameplay.civilizations.rome import Rome

if TYPE_CHECKING:
    from gameplay.age import Age
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
        self.width: int = width
        self.height: int = height
        self.player: Type[Civilization] = player
        self.enemies: Optional[List[Any]] = enemies
        self.generator: Type["BaseGenerator"] = generator
        self.generator_options: Dict[str, Any] = generator.get_default_setup_options()
        self.difficulty: int = difficulty
        self.num_enemies: int = num_enemies
        self.seed: Optional[int] = seed
        self.age: "Age | None" = None
        self.start_config: Dict[str, Any] = {}

    def __getstate__(self) -> object:
        return self.__dict__.copy()

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)

    def dump(self) -> dict[str, Any]:
        data: dict[str, Any] = self.__dict__.copy()
        data["player"] = f"{self.player.__module__}.{self.player.__class__}"
        if self.age is not None:
            data["age"] = self.age.dump()
        return data

    def load_state(self, data: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        self.age = EntityManager.dynamic_import(data.get("game.current_age").value.get("cls_ref"))  # type: ignore

    def set_age(self, age: "Age") -> None:
        self.age = age

    def get_age(self) -> "Age | None":
        return self.age
