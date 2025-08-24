from typing import Any, Callable, Dict, Optional, Self, Tuple

from direct.showbase import MessengerGlobal
from managers.combat import T_TARGET
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from managers.log import LogManager

"""Action system will provide a generic way to handle actions in the game. This will be used for units, buildings, and other game objects that can perform actions.

Actions cannot be stateful, they are meant to be stateless and only perform an action when called. They can have conditions to check if they can be run or not.
They can have properties that can be used to determine if they can be run or not. or while they are active have a state. but they should not be used to store state.
They wont be registered in the entity manager, they will be used as a one-off action. and therefore also not be saved to the save file.

Raises:
    ValueError: If the action has no callable action to run.
"""


class Action:
    debug_action: bool = False

    def __init__(
        self,
        name: T_TranslationOrStr,
        action: Callable[[Self, Any, Any], Optional[Any]],
        condition: Optional[Callable[[Self], bool] | bool] = None,
        on_success: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], Optional[bool]]] = None,
        on_failure: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], None]] = None,
        success_condition: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], bool]] = None,
        on_cancel: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], None]] = None,
        executor: Optional[T_TARGET] = None,
        icon: str | None = None,
        usable: bool = True,
        description: T_TranslationOrStrOrNone = None,
        *args: Tuple[Any, ...],
        **kwargs: Dict[str, Any],
    ):
        self.key: str = ""
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStrOrNone = description  # Might be used as a tooltip
        self.icon: str | None = icon
        self.useable: bool = usable
        self.logger = LogManager.get_singleton_instance().engine.getChild("actions")
        self.executor: Optional[T_TARGET] = executor

        self.condition: Optional[Callable[[Self], bool] | bool] = condition
        self.action: Callable[..., Optional[Any]] = action

        self.on_success: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], Optional[bool]]] = on_success
        self.on_failure: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], Optional[bool]]] = on_failure
        self.on_cancel: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], None]] = on_cancel
        self.success_condition: Optional[Callable[[Self, Tuple[Any], Dict[Any, Any]], bool]] = success_condition

        self.use_range: bool = False
        self.min_range: int = 0
        self.max_range: int = 0

        self.action_args: Tuple[Any, ...] = args
        self.action_kwargs: Dict[str, Any] = kwargs

        if executor is not None:
            self.action_kwargs["executor"] = executor

        self.get_return_as_failure_argument: bool = False

        self.on_the_spot_action: bool = True
        self.targeting_tile_action: bool = False
        self.targeting_unit_action: bool = False
        self.keep_targeting_after_use: bool = False

        self.remove_actions_after_use: bool = False
        self.failure_reason: Any = None
        self._is_disabled: bool | Callable[[], bool] = False
        self.auto_refresh_basic_elements: bool = True
        self.reset_every_turn: bool = True
        self.use_target_arrow: bool = False

        self.action_result: Optional[Any] = None

    @property
    def is_disabled(self) -> bool:
        if callable(self._is_disabled):
            return self._is_disabled()
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, value: bool | Callable[[], bool]) -> None:
        self._is_disabled = value

    def cancel(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel(self, self.action_args, self.action_kwargs)
        self.is_disabled = self.should_be_disabled()

    def on_turn_end(self, turn: int) -> None:
        if self.reset_every_turn:
            self.action_result = None
            self.is_disabled = False
        else:
            self.is_disabled = self.should_be_disabled()

    def should_be_disabled(self) -> bool:
        return False

    def get_result(self) -> Optional[Any]:
        return self.action_result

    def run(self) -> None:
        self.logger.info(f"Running action: {self.name}")
        condition_met: bool = True
        if isinstance(self.condition, bool):
            condition_met = self.condition
        elif isinstance(self.condition, Callable):
            condition_met = self.condition(self)

        if self.condition is not None and condition_met is False:
            if self.on_failure is not None:
                self.on_failure(self, self.action_args, self.action_kwargs)
            return

        # We actually run the action here
        self.action_result = self.action(self, **self.action_kwargs)

        if self.success_condition is not None:
            """We test for true as the system works that you can return anything that is not False to be a success and that will be passed to the on_success callback."""
            self.logger.info(f"Checking success condition for action: {self.name}")
            if self.success_condition(self, self.action_args, self.action_kwargs):
                if self.on_success is not None:
                    self.logger.info(f"Action: {self.name} was successful.")
                    self.on_success(self, self.action_args, self.action_kwargs)
            else:
                if self.on_failure is not None:
                    self.logger.info(f"Action: {self.name} was a failure.")
                    if self.get_return_as_failure_argument:
                        self.on_failure(self, self.action_args, self.action_kwargs)
                    else:
                        self.on_failure(self, self.action_args, self.action_kwargs)
            return

        if (
            self.action_result is not False
        ):  # Very important to check for False, as None is a valid return value. has to do with success condition check.
            self.logger.info(f"Action: {self.name} was successful.")
            if self.on_success is not None:
                self.logger.info(f"Action: {self.name} has on_success callback, running it.")
                self.on_success(self, self.action_args, self.action_kwargs)
        else:
            self.logger.info(f"Action: {self.name} was a failure.")
            if self.on_failure is not None:
                self.logger.info(f"Action: {self.name} has on_failure callback, running it.")
                self.on_failure(self, self.action_args, self.action_kwargs)

        if self.auto_refresh_basic_elements:
            self.logger.info(f"Action: {self.name} will refresh the action bar.")
            MessengerGlobal.messenger.send("ui.update.ui.refresh_basic_elements")

    def is_debug_action(self) -> bool:
        return self.debug_action
