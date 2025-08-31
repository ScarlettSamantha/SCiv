from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type, cast

from gameplay.actions.debug.debug_action import DebugAction
from helpers.paths import PathsHelper
from managers.action import ActionManager
from mixins.singleton import Singleton

if TYPE_CHECKING:
    pass


class DebugManager(Singleton):
    action_manager = ActionManager

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.__load()

    def __load(self):
        from system.pyload import PyLoad

        path: Path = PathsHelper.get_actions_dir() / "debug"

        classes: Dict[str, Type["DebugAction"]] = cast(
            Dict[str, Type["DebugAction"]], PyLoad.load_classes(str(path), package="gameplay.actions.debug")
        )
        for _, _cls in classes.items():
            if _cls is not DebugAction:
                self.register_debug_action(_cls)

    @classmethod
    def register_debug_action(cls, action: Type[DebugAction]) -> None:
        _action = action()
        cls.action_manager.register_action(_action, staged=True)

    @classmethod
    def get_debug_action(cls, key: str) -> DebugAction | None: ...

    @classmethod
    def unregister_debug_action(cls, key: str) -> None:
        cls.action_manager.unregister_action(key, staged=True)

    @classmethod
    def get_all_debug_actions(cls) -> Dict[str, DebugAction]:
        actions: Dict[str, DebugAction] = {}
        for key, value in cls.action_manager.get_staged_actions().items():
            if isinstance(value, DebugAction):
                actions[str(key)] = value
        return actions

    def enable_debug(self):
        self.debug_mode = True

    def disable_debug(self):
        self.debug_mode = False

    def is_debug_enabled(self):
        return self.debug_mode
