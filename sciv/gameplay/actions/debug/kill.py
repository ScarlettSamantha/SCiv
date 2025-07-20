from typing import Any

from gameplay.actions.debug.debug_action import DebugAction
from gameplay.unit import Unit
from managers.combat import T_TARGET

from sciv.gameplay.city import City
from sciv.gameplay.improvement import Improvement
from sciv.gameplay.player import Player


class KillAction(DebugAction):
    key = "actions.debug.kill"
    debug_action = True

    def __init__(self):
        super().__init__(
            name=self.key,
            action=self.kill_wrapper,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=self.is_successful,
        )
        self.on_the_spot_action = False
        self.targeting_unit_action = True
        self.keep_targeting_after_use = (
            True  # This is so we don't try to select a unit after killing which would cause a error.
        )

    def kill_wrapper(self, *args: Any, **kwargs: Any) -> None:
        target: T_TARGET | None = self.action_kwargs.get("target")
        if isinstance(target, Unit):
            target.kill()
            return
        raise ValueError("Target must be a Unit instance.")

    def is_successful(self, *args: Any, **kwargs: Any) -> bool:
        target: City | Player | Improvement | Unit | None = self.get_target()
        assert target is not None, "Target must be set before checking success."
        return not target.is_alive()

    def get_target(self) -> T_TARGET | None:
        return self.action_kwargs.get("target", None)
