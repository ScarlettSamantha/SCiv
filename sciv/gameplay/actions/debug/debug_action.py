from typing import Any, Callable, List, Optional, Self

from managers.i18n import T_TranslationOrStr
from system.actions import Action


class DebugAction(Action):
    key = "actions.debug.base"
    debug_action = True

    def __init__(
        self,
        action: Optional[Callable[[Self, Any, Any], Optional[Any]]] = None,
        name: T_TranslationOrStr = key,
        *args: List[Any],
        **kwargs: Any,
    ):
        if action is None:
            action = self.undefined_action
        super().__init__(name=name, action=action, *args, **kwargs)

    def undefined_action(
        self, *args: Any, **kwargs: Any
    ) -> None:  # This is done for syntax sugar as otherwise mypy would complain but child classes should implement this method or override the reference to this function.
        raise NotImplementedError("DebugAction must implement run_action method.")
