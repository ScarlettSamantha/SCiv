from abc import abstractmethod
from typing import TYPE_CHECKING, Any, List, Type

from gameplay.condition import CivicCondition, Condition, Conditions
from managers.i18n import T_TranslationOrStr
from mixins.callbacks import CallbacksMixin

if TYPE_CHECKING:
    from gameplay.civic import Civic


class Civic(CallbacksMixin):
    key: str
    name: T_TranslationOrStr
    description: T_TranslationOrStr
    requires: Conditions = Conditions()
    tier: int = 0
    unlocks: List[Type["Civic"]] = []

    def __init__(
        self,
        _cost: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        CallbacksMixin.__init__(self, *args, **kwargs)

        self.requires_civics: List["Civic"] = []
        self._cost: int = _cost
        self._progress: int = 0

        self.declare_callbacks()

    def declare_callbacks(self):
        self._declare_event("on_progress")
        self._declare_event("on_complete")

    @classmethod
    def add_requirement(cls, requirement: Condition | Type["Civic"]):
        if not isinstance(requirement, Condition):
            requirement = CivicCondition(requirement)

        if requirement in cls.requires:
            return

        cls.requires.add(requirement)

    @classmethod
    def get_tier(cls) -> int:
        return cls.tier

    @property
    def completed(self) -> bool:
        return self._completed

    @completed.setter
    def completed(self, value: bool):
        self._completed = value
        self.trigger_callback("on_complete")

    @property
    def cost(self) -> int:
        return self._cost

    @cost.setter
    def cost(self, value: int | float):
        if isinstance(value, float):
            self._cost = round(value)
        else:
            self._cost = value

    @property
    def progress(self) -> int:
        return self._progress

    @progress.setter
    def progress(self, value: int | float):
        if isinstance(value, float):
            self._progress = round(value)
        else:
            self._progress = value

        self.trigger_callback("on_progress")

        if self._progress >= self.cost:
            self.completed = True

    def is_requires_completed(self) -> bool:
        return self.requires()  # Call is evaluation

    @classmethod
    def get_requirements(cls) -> List[Type["Civic"]]:
        if not cls.requires:
            return []

        requirements: List[Type[Civic]] = []
        for requirement in cls.requires:
            if isinstance(requirement, CivicCondition):
                requirements.append(requirement.get_civic())
            else:
                continue
        return requirements

    @classmethod
    def get_unlocks(cls) -> List[Type["Civic"]]:
        return cls.unlocks

    def __add__(self, other: int):
        self.progress += other
        return self

    def __sub__(self, other: int):
        self.progress -= other
        return self

    def __mul__(self, other: int):
        self.progress = round(self.cost, other)
        return self

    def __truediv__(self, other: int):
        self.progress = round(self.cost / other)
        return self


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
