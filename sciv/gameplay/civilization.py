from abc import abstractmethod
from random import choice
from typing import Any, Dict, List, Self, Tuple, Type

from gameplay.effect import Effect
from gameplay.leader import Leader
from helpers.colors import Colors
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStr, get_i18n


class Civilization:
    name: T_TranslationOrStr = ""
    description: T_TranslationOrStr = ""
    introduction: T_TranslationOrStr = ""
    icon: str = Placeholder.getPlaceholderImagePathSmallIcon()
    city_names: List[T_TranslationOrStr] = []
    city_name_index: int = 0
    color: Tuple[float, float, float, float] = Colors.MAGENTA  # Default color

    def __init__(
        self,
    ) -> None:
        self.dynamic_name = self.name
        self._loadable = False
        self._leaders: List[Leader] = []

        self._effects: List[Effect] = []
        self.leader: Leader | None = None

        # Init registers
        self.register_effects()
        self.register_leaders()

    def effects(self) -> List[Effect]:
        return self._effects

    def add_effect(self, effect: Effect) -> None:
        self._effects.append(effect)

    def add_leader(self, leader: Leader) -> None:
        self.leaders.append(leader)

    @property
    def leaders(self) -> List[Leader]:
        return self._leaders

    @leaders.setter
    def leaders(self, leaders: List[Leader]) -> None:
        self._leaders = leaders

    @abstractmethod
    def register_effects(self) -> None:
        pass

    @abstractmethod
    def register_leaders(self) -> None:
        pass

    def random_leader(self) -> Leader:
        return choice(self.leaders)

    def get_city_name(self) -> str:
        return str(self.get_city_name_translation())

    def get_city_name_translation(self) -> T_TranslationOrStr:
        city_name = self.city_names[self.city_name_index]
        if self.city_name_index + 1 < len(self.city_names):
            self.city_name_index += 1
        else:
            self.city_name_index = 0  # Reset to 0 as we have reached the end of the list
        return city_name

    def __str__(self) -> str:
        leader_name_list: List[str] = []
        for leader in self.leaders:
            leader_name_list.append(str(leader.name) if leader.name else "Unknown")
        leaders: str = ", ".join(leader_name_list)
        return f"{self.name} - {self.description} <{leaders}>"

    def __call__(self) -> Self:
        return self

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "introduction": self.introduction,
            "icon": self.icon,
            "city_names": self.city_names,
            "city_name_index": self.city_name_index,
            "dynamic_name": self.dynamic_name,
            "leaders": [leader.dump() for leader in self.leaders],
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        self.name = (
            get_i18n().from_key(state.get("name", "").get("key", ""))
            if isinstance(state.get("name"), dict)
            else state.get("name", "")
        )
        self.description = get_i18n().from_key(state.get("description", ""))
        self.introduction = get_i18n().from_key(state.get("introduction", ""))
        self.icon = state.get("icon", Placeholder.getPlaceholderImagePathSmallIcon())
        self.city_names = [
            get_i18n().from_key(name.get("key")) if isinstance(name, dict) else name  # type: ignore
            for name in state.get("city_names", [])
        ]
        self.city_name_index = state.get("city_name_index", 0)
        self.dynamic_name = state.get("dynamic_name", self.name)

        leaders_data: List[Dict[str, Any]] = state.get("leaders", [])
        self.leaders = []
        for leader_data in leaders_data:
            _leader_class: Type[Leader] = EntityManager.get_singleton_instance().dynamic_import(
                leader_data.get("cls_ref", "Leader")
            )

            leader: Leader = _leader_class.__new__(_leader_class)
            leader.load_state(leader_data)
            self.add_leader(leader)
