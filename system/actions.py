from typing import Any, Callable, Dict, List, Optional, Self, Tuple

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class Action:
    def __init__(
        self,
        name: T_TranslationOrStr,
        action: Callable[[Self, Any, Any], Optional[bool]],
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

        self.action_result: Optional[Any] = None

    def get_result(self) -> Optional[Any]:
        return self.action_result

    def run(self):
        if self.action is not None:
            condition_met: bool = False
            if isinstance(self.condition, bool):
                condition_met = self.condition
            elif isinstance(self.condition, Callable):
                condition_met = self.condition(self)

            if self.condition is None or condition_met is False:
                return

            self.action_result = self.action(self, self.action_args, self.action_kwargs)

            if self.success_condition is not None:
                self.action_result = self.success_condition(self, self.action_args, self.action_kwargs)

            if self.action_result is None:
                return

            if self.action_result is True:
                if self.on_success is not None:
                    self.on_success(self, self.action_args, self.action_kwargs)
            else:
                if self.on_failure is not None:
                    if self.get_return_as_failure_argument:
                        self.on_failure(self, self.action_args, self.action_kwargs, self.action_result)
                    else:
                        self.on_failure(self, self.action_args, self.action_kwargs)

        else:
            raise ValueError("Action has no callable action to run.")
