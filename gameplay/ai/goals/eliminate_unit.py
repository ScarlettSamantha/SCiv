from typing import TYPE_CHECKING, Any, Dict

from gameplay.ai.core import Goal
from gameplay.ai.goal import T_PARENT
from gameplay.border import TileRepository
from gameplay.unit import CantMoveReason

if TYPE_CHECKING:
    from gameplay._units import Unit


class EliminateUnit(Goal):
    """
    EliminateUnit is a goal that represents the AI's objective to eliminate a specific unit.
    """

    name = "Eliminate Unit Goal"
    description = "Eliminate a specific unit"
    for_unit = True

    def __init__(
        self,
        target: "Unit",
        executing_unit: "Unit",
        parent: T_PARENT,
        *args: Dict[str, Any],
        **kwargs: Dict[str, Any],
    ):
        super().__init__(parent=parent, target=target, executing_unit=executing_unit, *args, **kwargs)
        self.name: str = "Eliminate Unit"
        self.description: str = f"Eliminate the unit {str(target.name)}"

    def is_achieved(self) -> bool:
        return self.get_target().is_alive() is False or super().is_achieved()

    def turn_tick(self) -> None:
        attacker = self.get_executing_unit()
        target = self.get_target()
        if not target.is_alive():
            return

        start_tile = attacker.get_tile()
        goal_tile = target.get_tile()
        movement_points_left = attacker.moves_left
        attack_range = getattr(attacker, "attack_range", 1)

        result = TileRepository.find_movable_attack_position(
            start_tile, goal_tile, movement_points_left, attack_range=attack_range
        )
        if not result:
            # no reachable attack‐position this turn
            return

        _, path = result
        # skip the first element (own tile)
        for step in path[1:]:
            if attacker.move(step) != CantMoveReason.COULD_MOVE:
                break

        # if we ended in range, fire
        if TileRepository.distance(attacker.get_tile(), goal_tile) <= attack_range:
            attacker.attack(target)

    def get_target(self) -> "Unit":
        return self.target  # type: ignore[return-value]
