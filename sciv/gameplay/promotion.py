from abc import abstractmethod
from typing import Any, Iterable, List, Self

from managers.i18n import T_TranslationOrStr
from system.requires import Requires, RequiresMultiple, T_Requires


class Promotion:
    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        icon: str,
        aquired: bool = False,
        requires: T_Requires = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description
        self.icon: str = icon
        self._requires: T_Requires = requires

        self.aquired: bool = aquired

    @property
    def requires(self) -> T_Requires:
        return self._requires

    @requires.setter
    def requires(self, requires: T_Requires) -> Self:
        if isinstance(requires, Iterable) and not isinstance(requires, (str, bytes)):
            # Convert Iterable to a list
            self._requires = RequiresMultiple.convert_from_list(requires)  # type: ignore
        else:
            self._requires = requires
        return self

    def are_requirements_met(self) -> bool:
        if self.requires is None:
            return True
        if isinstance(self.requires, (Requires, RequiresMultiple)):
            return self.requires.checkCondition()
        if isinstance(self.requires, list):
            return all(req.checkCondition() for req in self.requires)
        return False

    def aquire(self) -> "Promotion":
        self.aquired = True
        return self

    def unaquire(self) -> "Promotion":
        self.aquired = False
        return self

    def is_locked(self) -> bool:
        if self.requires is None:
            return False
        if isinstance(self.requires, (Requires, RequiresMultiple)):
            return self.requires.checkCondition()
        if isinstance(self.requires, list):
            return all(req.checkCondition() for req in self.requires)
        return False


class PromotionTree:
    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        icon: str,
        unlocked: bool = False,
        unlock_requires: T_Requires = None,
        *args: Any,
        **kwargs: Any,
    ):
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description
        self.promotions: List[Promotion] = []
        self.icon: str = icon
        self.requires: T_Requires = unlock_requires
        self.unlocked: bool = unlocked
        self.register_promotions()

    @abstractmethod
    def register_promotions(self) -> None:
        pass

    def add_promotion(self, promotion: Promotion) -> "PromotionTree":
        self.promotions.append(promotion)
        return self

    def remove_promotion(self, promotion: Promotion) -> "PromotionTree":
        self.promotions.remove(promotion)
        return self

    def is_locked(self) -> bool:
        if self.requires is None:
            return False
        if isinstance(self.requires, (Requires, RequiresMultiple)):
            return self.requires.checkCondition()
        if isinstance(self.requires, list):
            return all(req.checkCondition() for req in self.requires)
        return False

    def unlock(self) -> "PromotionTree":
        self.unlocked = True
        return self

    def lock(self) -> "PromotionTree":
        self.unlocked = False
        return self

    def completed(self) -> bool:
        return all([promotion.aquired for promotion in self.promotions])

    def stats(self) -> dict[str, bool | int]:
        return {
            "unlocked": self.unlocked,
            "num_promotions": len(self.promotions),
            "num_aquired": len([promotion for promotion in self.promotions if promotion.aquired]),
        }
