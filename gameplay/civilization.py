from abc import abstractmethod
from random import choice
from typing import List, Self

from gameplay.leader import Leader
from managers.i18n import T_TranslationOrStr
from system.effects import Effect


class Civilization:
    name: T_TranslationOrStr = ""
    description: T_TranslationOrStr = ""
    city_names: List[T_TranslationOrStr] = []
    city_name_index: int = 0

    def __init__(
        self,
    ) -> None:
        self.dynamic_name = self.name
        self.icon: str | None = None
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
