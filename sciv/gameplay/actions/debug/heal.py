from typing import Any

from gameplay.actions.debug.debug_action import DebugAction
from gameplay.unit import Unit
from managers.combat import T_TARGET


class HealAction(DebugAction):
    key = "actions.debug.heal"
    debug_action = True

    def __init__(self):
        super().__init__(
            name=self.key,
            action=self.heal_wrapper,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=self.is_successful,
        )
        self.on_the_spot_action = False
        self.targeting_unit_action = True
        self.keep_targeting_after_use = True  # This is so we dont try to select a unit after healing

    def heal_wrapper(self, *args: Any, **kwargs: Any) -> None:
        target: T_TARGET | None = self.action_kwargs.get("target")
        if isinstance(target, Unit):
            target.heal(target.max_health)  # Heal to full health
            return
        raise ValueError("Executor must be a Unit instance.")

    def is_successful(self, *args: Any, **kwargs: Any) -> bool:
        target: T_TARGET | None = self.action_kwargs.get("target")
        assert target is not None, "Target must be set before checking success."
        return target.health() == target.max_health
