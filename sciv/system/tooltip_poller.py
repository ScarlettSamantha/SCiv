import weakref
from typing import TYPE_CHECKING
from weakref import WeakSet

from direct.task import Task
from helpers.cache import Cache

if TYPE_CHECKING:
    from menus.kivy.elements.tooltip import TooltipBehavior


class TooltipPoller:
    _instance: "TooltipPoller | None" = None

    @classmethod
    def instance(cls) -> "TooltipPoller":
        if cls._instance is None:
            cls._instance = TooltipPoller()
        return cls._instance

    def __init__(self) -> None:
        self.base = Cache.get_showbase_instance()
        self._widgets: WeakSet["TooltipBehavior"] = weakref.WeakSet()
        self._task_name = "_tooltip__global_mouse_poll"
        self._polling = False
        self._delay = 1 / 10

    def register(self, widget: "TooltipBehavior") -> None:
        self._widgets.add(widget)
        self._ensure_task()

    def unregister(self, widget: "TooltipBehavior") -> None:
        if widget in self._widgets:
            self._widgets.discard(widget)
        if not self._widgets:
            self._stop_task()

    def _ensure_task(self) -> None:
        if not self._polling:
            self.base.taskMgr.add(self._poll, self._task_name, delay=self._delay)  # type: ignore
            self._polling = True

    def _stop_task(self) -> None:
        if self._polling:
            self.base.taskMgr.remove(self._task_name)
            self._polling = False

    def _poll(self, task: Task.Task) -> int:
        if not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            return Task.cont

        win_size = self.base.win.getSize()  # type: ignore
        px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
        py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore

        for w in list(self._widgets):
            try:
                if w.should_poll():
                    w.handle_global_mouse(px, py)
                else:
                    if w.tooltip_visible:
                        w.hide_tooltip()
                    w.hovered = False
            except Exception:
                pass  # nosec: B110
        return Task.cont
