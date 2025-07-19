from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Iterable, List, Union

from exceptions.condition_exception import ConditionObjectPropertyDoesNotExist

if TYPE_CHECKING:
    from gameplay.promotion import Promotion, PromotionTree
    from system.requires import Requires, RequiresMultiple


class Condition:
    def __init__(self, obj: object, property: str, required_value: Any, *args: Any, **kwargs: Any) -> None:
        self.obj: object = obj
        self.property: str = property
        self.required_value: Any = required_value

    def checkCondition(self) -> bool:
        if not hasattr(self.obj, self.property):
            raise ConditionObjectPropertyDoesNotExist(
                f"Object[{self.obj.__class__.__name__}] does not have property[{self.property}]"
            )

        _property_ref: Union[Callable[[], Any], Any] = getattr(self.obj, self.property)
        # If the property is a function, call it and compare the result to the required value
        if isinstance(_property_ref, Callable):
            return bool(_property_ref() == self.required_value)  # type: ignore

        return _property_ref == self.required_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[obj={self.obj}, property={self.property}, required_value={self.required_value}] -> {self.checkCondition()}"


class ConditionMultiple(Condition):
    def __init__(self, conditions: List[Condition], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.conditions: List[Condition] = conditions

    def checkCondition(self) -> bool:
        for condition in self.conditions:
            if not condition.checkCondition():
                return False
        return True


class Requires(Condition):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class RequiresMultiple(ConditionMultiple):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @classmethod
    def convert_from_list(cls, conditions: Requires) -> "RequiresMultiple":
        return cls(conditions=conditions)


class RequiresPromotionComplete(Requires):
    def __init__(self, promotion: "Promotion", *args: Any, **kwargs: Any):
        super().__init__(obj=promotion, property="acquired", required_value=True, *args, **kwargs)


class RequiresPromotionsComplete(RequiresMultiple):
    def __init__(self, promotions: List["Promotion"], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for promotion in promotions:
            _instance: RequiresPromotionComplete = RequiresPromotionComplete(promotion=promotion)
            self.conditions.append(_instance)


class RequiresPromotionTreeUnlocked(Requires):
    def __init__(self, promotion_tree: "PromotionTree", *args: Any, **kwargs: Any) -> None:
        super().__init__(
            obj=promotion_tree,
            property="unlocked",
            required_value=True,
            *args,
            **kwargs,
        )


class RequiresPromotionTreesUnlocked(RequiresMultiple):
    def __init__(self, promotion_trees: List["PromotionTree"], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for promotion_tree in promotion_trees:
            _instance: RequiresPromotionTreeUnlocked = RequiresPromotionTreeUnlocked(promotion_tree=promotion_tree)
            self.conditions.append(_instance)


T_Requires = Union[Requires, RequiresMultiple, Iterable[Requires], None]
