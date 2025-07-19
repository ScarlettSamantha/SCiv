from typing import TYPE_CHECKING, Any, Dict, Generator, List, Tuple, Type

from gameplay.age import Age
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStr, t_

if TYPE_CHECKING:
    from gameplay.player import Player
    from system.entity import BaseEntity


class Tech:
    requires: List[Type["Tech"]] = []
    key: str
    name: T_TranslationOrStr | None = None
    description: T_TranslationOrStr | None = None

    _icon: T_TranslationOrStr | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.TIEL

    tech_points_required: int = 1
    age: Age | None = None
    color: Tuple[int, int, int, int] | None = None
    contributes_to: List[Type["Tech"]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.key: str = self.key

        self.name: T_TranslationOrStr | None = self.name if self.name is not None else t_(f"tech.{self.key}.name")
        self.description: T_TranslationOrStr | None = (
            self.description if self.description is not None else t_(f"tech.{self.key}.description")
        )
        self.icon: T_TranslationOrStr | None = (
            self.description if self.description is not None else t_(f"tech.{self.key}.description")  # type: ignore
        )
        self.color: Tuple[int, int, int, int] | None = self.color

        self.completed = False
        self.tech_points_required: int = self.tech_points_required
        self.age: Age | None = self.age

    def __repr__(self, recursive: bool = False):
        return f"{self.name}"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Tech):
            return self.name == other.name
        return False

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        return [] + cls.contributes_to  # type: ignore

    @classmethod
    def on_tooltip(cls) -> str:
        return f"[b]{str(cls.name)}[/b]\n\n[i]Costs:[/i] {cls.tech_points_required} points\n\n{str(cls.description)}"  # type: ignore

    @classmethod
    def get_icon(cls) -> T_TranslationOrStr:
        return cls._icon if cls._icon is not None else Placeholder.getPlaceholderImagePathSmallIcon()

    @classmethod
    def set_icon(cls, value: T_TranslationOrStr) -> None:
        cls._icon = value

    def on_unlock(self, player: "Player") -> None: ...

    def dump(self) -> Dict[str, Any]:
        return {
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        pass


class TechTree:
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    icon: T_TranslationOrStr | None = None

    def __init__(self):
        self._items: List[Type[Tech]] = []
        self._ages: List[Age] = []  # noqa F821

    def items(self) -> Generator[Type[Tech], None, None]:
        for item in self._items:
            yield item

    def add(self, item: Type[Tech]) -> None:
        self._items.append(item)

    def add_age(self, age: Age) -> None:
        self._ages.append(age)

    def dump(self) -> Dict[str, Any]:
        data = {
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "items": [f"{item.__module__}.{item.__name__}" for item in self._items],
        }
        return data

    def load_state(self, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        self.key = state.get("key", "")
        self.name = state.get("name", "")
        self.description = state.get("description", "")
        self.icon = state.get("icon", None)

        self._items = [EntityManager.dynamic_import(item) for item in state.get("items", [])]
