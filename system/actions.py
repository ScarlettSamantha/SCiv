from typing import Any, Callable, Dict, List, Optional, Self, Tuple

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
    def __init__(
        self,
        name: T_TranslationOrStr,
        action: Callable[[Self, Any, Any], Optional[Any]],
        condition: Optional[Callable[[Self], bool] | bool] = None,
        on_success: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = None,
        on_failure: Optional[Callable[[Self, Tuple, Dict], None]] = None,
        success_condition: Optional[Callable[[Self, Tuple, Dict], bool]] = None,
        icon: str | None = None,
        usable: bool = True,
        description: T_TranslationOrStrOrNone = None,
        *args,
        **kwargs,
    ):
        self.key: str = ""
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStrOrNone = description  # Might be used as a tooltip
        self.icon: str | None = icon
        self.useable: bool = usable
        self.logger = LogManager.get_instance().engine.getChild("actions")

        self.condition: Optional[Callable[[Self], bool] | bool] = condition
        self.action: Callable[[Self, List | Tuple, Dict], Optional[bool]] = action

        self.on_success: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = on_success
        self.on_failure: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = on_failure
        self.success_condition: Optional[Callable[[Self, Tuple, Dict], bool]] = success_condition

        self.action_args: Tuple[Any] = args
        self.action_kwargs: Dict[str, Any] = kwargs

        self.get_return_as_failure_argument: bool = False

        self.on_the_spot_action: bool = True
        self.targeting_tile_action: bool = False
        self.targeting_unit_action: bool = False

        self.remove_actions_after_use: bool = False
        self.failure_reason: Any = None

        self.action_result: Optional[Any] = None

    def get_result(self) -> Optional[Any]:
        return self.action_result

    def run(self):
        self.logger.info(f"Running action: {self.name}")
        if self.action is not None:
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
            self.action_result = self.action(self, self.action_args, self.action_kwargs)

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
            ):  # Very important to check for False, as None is a valid return value. has to do with sucess condition check.
                self.logger.info(f"Action: {self.name} was successful.")
                if self.on_success is not None:
                    self.logger.info(f"Action: {self.name} has on_success callback, running it.")
                    self.on_success(self, self.action_args, self.action_kwargs)
            else:
                self.logger.info(f"Action: {self.name} was a failure.")
                if self.on_failure is not None:
                    self.logger.info(f"Action: {self.name} has on_failure callback, running it.")
                    self.on_failure(self, self.action_args, self.action_kwargs)

        else:
            raise ValueError("Action has no callable action to run.")
