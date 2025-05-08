from typing import TYPE_CHECKING, Any, Dict

from gameplay.ai.core import Goal
from gameplay.ai.goal import T_PARENT
from gameplay.border import TileRepository

if TYPE_CHECKING:
    from gameplay._units import UnitBaseClass


class EliminateUnit(Goal):
    """
    EliminateUnit is a goal that represents the AI's objective to eliminate a specific unit.
    """

    name = "Eliminate Unit Goal"
    description = "Eliminate a specific unit"
    for_unit = True

    def __init__(
        self,
        target: "UnitBaseClass",
        executing_unit: "UnitBaseClass",
        parent: T_PARENT,
        *args: Dict[str, Any],
        **kwargs: Dict[str, Any],
    ):
        super().__init__(parent=parent, target=target, executing_unit=executing_unit, *args, **kwargs)
        self.name: str = "Eliminate Unit"
        self.description: str = f"Eliminate the unit {str(target.name)}"

    def turn_tick(self) -> None:
        if not self.get_target().is_alive():
            self.mark_achieved()
            return

        target_tile = self.target.get_tile()
        current_tile = self.get_executing_unit().get_tile()
        if (path := TileRepository.astar(current_tile, target_tile, self.get_executing_unit().moves_left)) is not None:
            if len(path) > 1:
                for tile in path:
                    self.get_executing_unit().move(tile)
            else:
                self.get_executing_unit().attack(self.target)

    def get_target(self) -> "UnitBaseClass":
        return self.target  # type: ignore[return-value]
