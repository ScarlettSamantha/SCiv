from typing import TYPE_CHECKING, Iterator, Type, Optional, Union
from weakref import ReferenceType
from exceptions.ai import AIException

if TYPE_CHECKING:
    from gameplay._units import Unit
    from gameplay.ai.core import AI
    from gameplay.cities import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player


T_TARGET = Union["City", "Player", "Improvement", "Unit"]
T_PARENT = Union[ReferenceType["AI"], "AI"]


class Goal:
    name: str
    description: str
    for_unit: bool = False
    needs_turn_processing: bool = True

    def __init__(self, parent: T_PARENT, target: T_TARGET, executing_unit: Optional["Unit"] = None):
        self.executing_unit: Optional["Unit"] = executing_unit
        self.target: T_TARGET = target
        self.parent_ai: ReferenceType["AI"] = parent if isinstance(parent, ReferenceType) else ReferenceType(parent)
        self.achieved: bool = False

    def turn_tick(self) -> None: ...

    def get_parent(self) -> "AI":
        resolved_reference = self.parent_ai()
        if resolved_reference is None:
            raise AIException("Parent AI reference is None")
        return resolved_reference

    def is_for_unit(self) -> bool:
        """Check if the goal is for a specific unit."""
        return self.for_unit

    def get_executing_unit(self) -> "Unit":
        """Get the executing unit for this goal."""
        if self.executing_unit is None and self.for_unit:
            raise AIException("Executing unit is None when for_unit is True")
        return self.executing_unit  # type: ignore

    def get_target(self) -> T_TARGET:
        """Get the target for this goal."""
        return self.target

    def is_achieved(self) -> bool:
        """Check if the goal is achieved."""
        return self.achieved

    def mark_achieved(self) -> None:
        """Mark the goal as achieved."""
        self.achieved = True

    def not_achieved(self) -> None:
        """Mark the goal as not achieved."""
        self.achieved = False


class Goals:
    def __init__(self):
        self.goals: list[Goal] = []
        self.removed_goals: list[Goal] = []

    def add_goal(self, goal: Goal) -> None:
        self.goals.append(goal)

    def remove_goal(self, goal: Goal, add_to_removed_list: bool = True) -> None:
        self.goals.remove(goal)
        if add_to_removed_list:
            self.removed_goals.append(goal)

    def get_goals(self) -> list[Goal]:
        return self.goals

    def has_goal(self, goal: Type[Goal] | Goal) -> bool:
        """Check if a specific goal is present in the list of goals."""
        if isinstance(goal, type):
            return any(isinstance(g, goal) for g in self.goals)
        return goal in self.goals

    def has_goal_for_unit(self, executing_unit: "Unit", goal_type: Optional[Type[Goal]] = None) -> bool:
        """
        Check if a specific unit has a goal of a certain type.
        If goal_type is None, check for any goal for the unit.
        """
        for goal in self.goals:
            if goal.for_unit and hasattr(goal, "executing_unit") and goal.executing_unit == executing_unit:
                if goal_type is None or isinstance(goal, goal_type):
                    return True
        return False

    def __iter__(self) -> Iterator[Goal]:
        return iter(self.goals)

    def __len__(self) -> int:
        return len(self.goals)
