from typing import Self, List
from gameplay.effect import Effects, Effect
from gameplay.leader import Leader
from managers.i18n import T_TranslationOrStr
from abc import abstractmethod
from random import choice


class Civilization:
    name: T_TranslationOrStr = ""
    description: T_TranslationOrStr = ""

    def __init__(
        self,
    ) -> None:
        self.dynamic_name = self.name
        self.icon: str | None = None
        self._loadable = False
        self._leaders: List[Leader] = []

        self._effects: Effects = Effects()
        self.leader: Leader | None = None

        # Init registers
        self.register_effects()
        self.register_leaders()

    def effects(self) -> Effects:
        return self._effects

    def add_effect(self, effect: Effect) -> None:
        self._effects.add(effect=effect, key_or_auto=str(effect.name))

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

    def __str__(self) -> str:
        leader_name_list: List[str] = []
        for leader in self.leaders:
            leader_name_list.append(str(leader.name) if leader.name else "Unknown")
        leaders: str = ", ".join(leader_name_list)
        return f"{self.name} - {self.description} <{leaders}>"

    def __call__(self) -> Self:
        return self
