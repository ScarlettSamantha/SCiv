from typing import Any, Callable, Dict, List, Optional, Self, Tuple
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class Action:
    def __init__(
        self,
        name: T_TranslationOrStr,
        action: Callable[[Self, Any, Any], Optional[bool]],
        condition: Optional[Callable[[Self], bool]] = None,
        on_success: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = None,
        on_failure: Optional[Callable[[Self, Tuple, Dict], None]] = None,
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

        self.condition: Optional[Callable[[Self], bool]] = condition
        self.action: Callable[[Self, List | Tuple, Dict], Optional[bool]] = action

        self.on_success: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = on_success
        self.on_failure: Optional[Callable[[Self, Tuple, Dict], Optional[bool]]] = on_failure

        self.action_args: Tuple[Any] = args
        self.action_kwargs: Dict[str, Any] = kwargs

    def run(self):
        if self.action is not None and (self.condition is None or self.condition(self) is True):
            result = self.action(self, self.action_args, self.action_kwargs)

            if result is None:
                return

            if result is True:
                if self.on_success is not None:
                    self.on_success(self, self.action_args, self.action_kwargs)
            else:
                if self.on_failure is not None:
                    self.on_failure(self, self.action_args, self.action_kwargs)

        else:
            raise ValueError("Action has no callable action to run.")
