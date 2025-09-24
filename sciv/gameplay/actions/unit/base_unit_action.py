from typing import Any

from system.actions import Action


class BaseUnitAction(Action):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.has_movement_point_cost: bool = False
        self.has_movement_point_left_requirement: bool = False

        self.movement_point_cost: float = 0.0
        self.movement_point_left_requirement: float = 0.0
