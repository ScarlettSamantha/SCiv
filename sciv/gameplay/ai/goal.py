from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Self, Tuple, Type, Union, cast
from weakref import ReferenceType, ref

from exceptions.ai import AIException
from managers.entity import EntityManager, EntityType
from system.entity import BaseEntity
from system.game_settings import GameSettings
from system.mesh import HexGrid

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

    def dump(self) -> Dict[str, Union[str, Any]]:
        parent_id: "AI | None" = self.parent_ai()

        if parent_id is None:
            raise AIException("Parent AI reference is None, cannot dump goal")

        player: "Player | None" = parent_id.get_player()

        return {
            "name": self.name,
            "description": self.description,
            "for_unit": self.for_unit,
            "needs_turn_processing": self.needs_turn_processing,
            "achieved": self.achieved,
            "target": self.target.get_tag(),
            "target_entity_type": self.target.get_entity_type(),
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "player": player.get_tag(),
        }

    @classmethod
    def load_state(cls, state: Dict[str, Any]) -> Self:
        instance: Self = cls.__new__(cls)

        instance.name = state.get("name", "")
        instance.description = state.get("description", "")
        instance.for_unit = state.get("for_unit", False)
        instance.needs_turn_processing = state.get("needs_turn_processing", True)
        instance.achieved = state.get("achieved", False)
        target_tag = state.get("target")
        target_type = state.get("target_type")
        player_tag = state.get("player")

        if target_tag is None or player_tag is None or target_type is None:
            raise AIException("Target(type) or player tag is None, cannot load state")

        player: ReferenceType[Player] | None = cast(
            ReferenceType[Player] | None,
            EntityManager.get_singleton_instance().get_ref_weak(EntityType.PLAYER, player_tag),
        )
        if player is None:
            raise AIException(f"Player with tag {player_tag} not found, cannot load state")

        _player: Player | None = player()
        assert _player is not None, f"Player with tag {player_tag} reference is None, cannot load state"
        instance.parent_ai = ref(_player.get_ai())

        search_results: Tuple[EntityType, BaseEntity | HexGrid | GameSettings] | None = (
            EntityManager.get_singleton_instance().search_key(key=target_tag)
        )

        assert search_results is not None, f"Search results for target with tag {target_tag} is None, cannot load state"
        assert isinstance(search_results[1], BaseEntity), (
            f"Search results for target with tag {target_tag} is not of type UNIT, cannot load state"
        )

        instance.target = cast(T_TARGET, search_results[1])

        return instance

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

    def dump(self) -> Dict[str, Any]:
        return {
            "goals": [goal.dump() for goal in self.goals],
            "removed_goals": [goal.dump() for goal in self.removed_goals],
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.goals = []
        self.removed_goals = []

        for goal_state in state.get("goals", []):
            goal_class = goal_state.get("cls_ref")

            if goal_class is None:
                raise AIException("Goal class reference is None, cannot load state")

            cls_type: Type[Goal] = cast(Type[Goal], EntityManager.dynamic_import(goal_class))
            goal_instance: Goal = cls_type.load_state(goal_state)
            self.goals.append(goal_instance)

        for removed_goal_state in state.get("removed_goals", []):
            goal_class = removed_goal_state.get("cls_ref")

            if goal_class is None:
                raise AIException("Removed goal class reference is None, cannot load state")

            cls_type: Type[Goal] = cast(Type[Goal], EntityManager.dynamic_import(goal_class))
            removed_goal_instance: Goal = cls_type.load_state(removed_goal_state)
            self.removed_goals.append(removed_goal_instance)
