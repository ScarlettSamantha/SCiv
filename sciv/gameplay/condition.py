from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Self, Type

from managers.player import PlayerManager

if TYPE_CHECKING:
    from gameplay.civic import Civic, CivicSubtree, CivicTree
    from gameplay.player import Player
    from gameplay.tech import Tech
    from gameplay.tile import Tile
    from gameplay.improvement import Improvement


class ConditionalTypes(Enum):
    AND = 0
    OR = 1


class Condition:
    def __init__(self, *args: Any, **kwargs: Any):
        self._condition: Optional[Callable[..., bool]] = None
        self.params: Dict[str, Any] = kwargs
        self.required_params: List[str] = []
        self._validate_params()

    def _validate_params(self) -> None:
        """Check if all required parameters are provided."""
        missing_params = [param for param in self.required_params if param not in self.params]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    def set(self, condition: Callable[..., bool]) -> None:
        """Set the condition function."""
        self._condition = condition

    def _invoke_condition(self) -> bool:
        """Invoke the condition function safely."""
        if self._condition is None:
            return True

        try:
            return self._condition(**self.params)  # Unpacking self.params
        except TypeError as e:
            raise TypeError(f"Error invoking condition function: {e}") from e

    def is_met(self) -> bool:
        """Evaluate the condition function safely."""
        return self._invoke_condition()

    def __call__(self, *args: Any, **kwargs: Any) -> bool:
        """Invoke the condition check."""
        return self.is_met()

    @classmethod
    def no_condition(cls) -> Self:
        """Return a no-op condition."""
        return cls()


class Conditions:
    def __init__(self, conditions: Optional[List[Condition] | Condition] = None, *args: Any, **kwargs: Any):
        self._conditions: List[Condition] = []
        self.conditional_type: ConditionalTypes = ConditionalTypes.AND
        self.condition_params: Dict[str, Any] = {}

        if conditions is not None:
            if isinstance(conditions, list):
                self._conditions.extend(conditions)
            else:
                self._conditions.append(conditions)

    def are_met(self, params: Dict[str, Any] = {}) -> bool:
        self.condition_params.update(params)
        """Evaluate all conditions based on the conditional type."""
        if self.conditional_type == ConditionalTypes.AND:
            for condition in self._conditions:
                if not condition(**self.condition_params):
                    return False
            return True
        elif self.conditional_type == ConditionalTypes.OR:
            for condition in self._conditions:
                if condition(**self.condition_params):
                    return True
            return False

        else:
            raise ValueError("Invalid conditional type")

    def add(self, condition: Condition) -> None:
        """Add a condition to the list."""
        self._conditions.append(condition)

    def remove(self, condition: Condition) -> None:
        """Remove a condition from the list."""
        self._conditions.remove(condition)

    def set_or(self) -> None:
        """Set the conditional type to OR."""
        self.conditional_type = ConditionalTypes.OR

    def set_and(self) -> None:
        """Set the conditional type to AND."""
        self.conditional_type = ConditionalTypes.AND

    def __call__(self, *args: Any, **kwargs: Any) -> bool:
        """Invoke the conditions check."""
        return self.are_met(params=self.condition_params)

    def __iter__(self) -> Iterator[Condition]:
        """Iterate over the conditions."""
        return iter(self._conditions)

    @classmethod
    def no_conditions(cls) -> Self:
        """Return a no-op conditions group."""
        return cls()


class BuildCondition(Condition):
    def __init__(self, tile: "Tile", improvement: Type["Improvement"], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.required_params = ["tile", "improvement"]
        self.params["tile"] = tile
        self.params["improvement"] = improvement
        self._condition = self._build_condition

    def _build_condition(self, tile: "Tile", improvement: Type["Improvement"]) -> bool:
        return tile.improvements().has(improvement) or (
            tile.city is not None and tile.city.get_improvements().has(improvement)
        )


class ResearchCondition(Condition):
    def __init__(
        self, tech: List[Type["Tech"]] | Type["Tech"], player: Optional["Player"] = None, *args: Any, **kwargs: Any
    ):
        if not isinstance(tech, list):
            tech = [tech]
        super().__init__(*args, **kwargs)
        self.params["tech"] = tech
        self.params["player"] = player
        self.required_params = ["player", "tech"]
        self._condition = self._research_condition

    def _research_condition(self, player: Optional["Player"], tech: List[Type["Tech"]]) -> bool:
        """Check if the player has researched the tech."""
        if player is None:
            player = PlayerManager.session_player()

        for t in tech:
            if not player.has_researched_tech(t):
                return False
        return True


class CivicTreeUnlockedCondition(Condition):
    def __init__(self, civic_tree: Type["CivicTree"], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.params["civic_tree"] = civic_tree
        self.required_params = ["civic_tree"]
        self._condition = self._civic_tree_unlocked_condition

    def _civic_tree_unlocked_condition(self, civic_tree: Type["CivicTree"], player: Optional["Player"] = None) -> bool:
        """Check if the player has unlocked the civic tree."""
        if player is None:
            player = PlayerManager.session_player()
        return player.has_civic_tree_unlocked(civic_tree)


class CivicSubTreeUnlockedCondition(Condition):
    def __init__(self, civic: Type["CivicSubtree"], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.params["civic"] = civic
        self.required_params = ["civic"]
        self._condition = self._civic_subtree_unlocked_condition

    def _civic_subtree_unlocked_condition(self, civic: Type["CivicSubtree"], player: Optional["Player"] = None) -> bool:
        """Check if the player has unlocked the civic subtree."""
        if player is None:
            player = PlayerManager.session_player()
        return player.has_civic_subtree_unlocked(civic)


class CivicCondition(Condition):
    def __init__(self, civic: Type["Civic"], player: Optional["Player"] = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.params["civic"] = civic
        self.params["player"] = player
        self.required_params = ["player", "civic"]
        self._condition = self._civic_condition

    def _civic_condition(self, civic: Type["Civic"], player: Optional["Player"] = None) -> bool:
        """Check if the player has researched the civic."""
        if player is None:
            player = PlayerManager.session_player()

        return player.has_civic(civic)

    def get_civic(self) -> Type["Civic"]:
        """Get the civic associated with this condition."""
        return self.params.get("civic")  # type: ignore
