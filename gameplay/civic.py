from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Self, Type

from gameplay.condition import CivicCondition, Condition, Conditions
from managers.i18n import T_TranslationOrStr

if TYPE_CHECKING:
    from gameplay.civic import Civic


class Civic:
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    requires: Dict[str, Conditions] = {}
    tier: int = 0
    unlocks: List[Type["Civic"]] = []
    base_cost: int = 10

    def __init__(
        self,
        cost_modifier: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.requires_civics: List["Civic"] = []
        self._cost: int = (self.base_cost * (self.tier if self.tier != 0 else 1)) + cost_modifier
        self._completed: bool = False

    @classmethod
    def add_requirement(cls, requirement: Condition | Type["Civic"]):
        if not isinstance(requirement, Condition):
            requirement = CivicCondition(requirement)

        if cls.key not in list(cls.requires.keys()):
            cls.requires[cls.key] = Conditions()
        elif requirement in cls.requires[cls.key]:
            return

        cls.requires[cls.key].add(requirement)

    @classmethod
    def set_requirements(cls, requirements: List[Condition | Type["Civic"]]):
        cls.requires[cls.key] = Conditions()

        if cls.key not in list(cls.requires.keys()):
            cls.requires[cls.key] = Conditions()

        for requirement in requirements:
            if not isinstance(requirement, Condition):
                requirement = CivicCondition(requirement)
            cls.requires[cls.key].add(requirement)

    @classmethod
    def get_tier(cls) -> int:
        return cls.tier

    @property
    def completed(self) -> bool:
        return self._completed

    @completed.setter
    def completed(self, value: bool):
        self._completed = value

    @property
    def cost(self) -> int:
        return self._cost

    @cost.setter
    def cost(self, value: int | float):
        if isinstance(value, float):
            self._cost = round(value)
        else:
            self._cost = value

    def is_requires_completed(self) -> bool:
        if not self.requires or self.key not in self.requires:
            return True
        return self.requires[self.key]()  # Call is evaluation

    @classmethod
    def get_requirements(cls) -> List[Type["Civic"]]:
        if not cls.requires or cls.key not in cls.requires:
            return []

        requirements: List[Type[Civic]] = []
        for requirement in cls.requires[cls.key]:
            if isinstance(requirement, CivicCondition):
                requirements.append(requirement.get_civic())
            else:
                continue
        return requirements

    @classmethod
    def get_unlocks(cls) -> List[Type["Civic"]]:
        return cls.unlocks

    def get_cost(self) -> int:
        return self.cost

    def complete(self) -> Self:
        self.completed = True
        return self

    @classmethod
    def is_unlockable(cls) -> bool:
        if cls.key in cls.requires.keys():
            return cls.requires[cls.key].are_met()
        return True


class CivicSubtree:
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    civics: List[Type[Civic]] = []
    order: int = 0

    @classmethod
    @abstractmethod
    def register_civics(cls) -> List[Type[Civic]]:
        pass

    @classmethod
    def add_civic(cls, civic: Type[Civic]):
        cls.civics.append(civic)

    def is_completed(self) -> bool:
        return all(civic.completed for civic in self.civics)

    @classmethod
    def get_all_civics(cls) -> List[Type[Civic]]:
        return cls.civics

    @classmethod
    def is_unlocked(cls) -> bool:
        return True


class CivicTree:
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self.subtrees: List[Type[CivicSubtree]] = []
        self.register_subtrees()

    @abstractmethod
    def register_subtrees(self):
        pass

    def add_subtree(self, subtree: Type[CivicSubtree]):
        self.subtrees.append(subtree)

    def get_all_civics(self) -> List[Type[Civic]]:
        civics: List[Type[Civic]] = []
        for subtree in self.subtrees:
            civics.extend(subtree.get_all_civics())
        return civics

    def get_all_subtrees(self) -> List[Type[CivicSubtree]]:
        return self.subtrees
