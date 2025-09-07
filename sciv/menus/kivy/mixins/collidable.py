import weakref
from time import time
from typing import TYPE_CHECKING, Dict, List, Tuple

from direct.task.Task import Task
from gameplay.city import messenger
from helpers.cache import Cache
from kivy.uix.layout import Layout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from managers.input import Input

if TYPE_CHECKING:
    from game import OpenCiv


class _CollisionPoller:
    _instance: "_CollisionPoller | None" = None

    @classmethod
    def instance(cls) -> "_CollisionPoller":
        if cls._instance is None:
            cls._instance = _CollisionPoller()
        return cls._instance

    def __init__(self) -> None:
        self.base: "OpenCiv" = Cache.get_showbase_instance()
        self._widgets: weakref.WeakSet[CollisionPreventionMixin] = weakref.WeakSet()

        self._mouse_task = "_collision__global_mouse_poll"
        self._geom_task = "_collision__global_ui_cache"

        self._mouse_running = False
        self._geom_running = False

        self._default_mouse_delay = 0.5
        self._default_geom_delay = 1.0

    def register(self, widget: "CollisionPreventionMixin") -> None:
        self._widgets.add(widget)
        self._ensure_tasks()

    def unregister(self, widget: "CollisionPreventionMixin") -> None:
        if widget in self._widgets:
            self._widgets.discard(widget)
        if not self._widgets:
            self._stop_tasks()

    def _ensure_tasks(self) -> None:
        if not self._mouse_running:
            self.base.taskMgr.add(self._mouse_poll, self._mouse_task)  # type: ignore
            self._mouse_running = True
        if not self._geom_running:
            self.base.taskMgr.add(self._geom_poll, self._geom_task)  # type: ignore
            self._geom_running = True

    def _stop_tasks(self) -> None:
        if self._mouse_running:
            self.base.taskMgr.remove(self._mouse_task)
            self._mouse_running = False
        if self._geom_running:
            self.base.taskMgr.remove(self._geom_task)
            self._geom_running = False

    def _mouse_delay(self) -> float:
        delays = [max(0.05, w.tick_rate) for w in self._widgets if w.should_poll_mouse()]
        return min(delays) if delays else self._default_mouse_delay

    def _geom_delay(self) -> float:
        delays = [max(0.2, w.ui_geometry_update_interval) for w in self._widgets if w.should_update_geometry()]
        return min(delays) if delays else self._default_geom_delay

    def _mouse_poll(self, task: Task) -> int:
        if not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            task.delayTime = self._mouse_delay()
            return Task.again

        win = self.base.win  # type: ignore
        mw = self.base.mouseWatcherNode  # type: ignore
        win_w, win_h = win.getXSize(), win.getYSize()
        px = (mw.getMouseX() + 1) * 0.5 * win_w
        py = (mw.getMouseY() + 1) * 0.5 * win_h

        for w in list(self._widgets):
            try:
                if w.should_poll_mouse():
                    w.handle_global_mouse(px, py)
                else:
                    w.ensure_not_colliding()
            except Exception:
                pass  # nosec: B110

        task.delayTime = self._mouse_delay()
        return Task.again

    def _geom_poll(self, task: Task) -> int:
        for w in list(self._widgets):
            try:
                if w.should_update_geometry():
                    w.update_ui_geometry_cache()
            except Exception:
                pass  # nosec: B110

        task.delayTime = self._geom_delay()
        return Task.again


class CollisionPreventionMixin:
    tick_rate: float = 0.5
    ui_geometry_update_interval: float = 1.0
    state_change_cooldown: float = 0.5

    def __init__(self, base: "OpenCiv", disable_zoom: bool = False) -> None:
        try:
            super().__init__()
        except Exception:
            pass  # nosec: B110

        self._input = Input.get_singleton_instance()
        self._base: "OpenCiv" = base
        self.disable_zoom: bool = disable_zoom

        self.non_collidable_ui: List[Widget | Layout | Popup] = []
        self.ui_geometry_cache: Dict[object, Tuple[float, float, float, float]] = {}

        self.last_raycaster_state: bool | None = None
        self.last_zoom_state: bool | None = None

        self.last_state_change_time: float = 0.0
        self.in_collision_with_ui: bool = False

        self._was_pollworthy: bool = False

        _CollisionPoller.instance().register(self)

    def should_poll_mouse(self) -> bool:
        if not self.non_collidable_ui:
            return False
        try:
            if self._base is None or self._base.win is None:  # type: ignore
                return False
        except Exception:
            return False
        return True

    def should_update_geometry(self) -> bool:
        return bool(self.non_collidable_ui)

    def handle_global_mouse(self, px: float, py: float) -> None:
        screen_x: int = int(px)
        screen_y: int = int((1 - self._base.mouseWatcherNode.getMouseY()) * 0.5 * self._base.win.getYSize())  # type: ignore

        self.on_mouse_move(screen_x, screen_y)

        self._was_pollworthy = True

    def ensure_not_colliding(self) -> None:
        if self._was_pollworthy:
            if self.in_collision_with_ui:
                self._set_input_state(raycaster=True, zoom_disabled=not self.disable_zoom)
            self._was_pollworthy = False

    def update_ui_geometry_cache(self) -> None:
        cache: Dict[object, Tuple[float, float, float, float]] = {}

        for element in list(self.non_collidable_ui):
            try:
                parent = element.parent  # type: ignore
                if not parent:
                    continue

                real_width: int = int(
                    element.size_hint_x * parent.width if getattr(element, "size_hint_x", None) else element.width  # type: ignore
                )  # type: ignore
                real_height: int = int(
                    element.size_hint_y * parent.height if getattr(element, "size_hint_y", None) else element.height  # type: ignore
                )  # type: ignore

                ui_x, ui_y = element.to_window(element.x, element.y)  # type: ignore[attr-defined]
                ui_right: int = int(ui_x + real_width)  # type: ignore
                ui_top: int = int(ui_y + real_height)  # type: ignore

                cache[element] = (ui_x, ui_y, ui_right, ui_top)
            except Exception:
                continue

        self.ui_geometry_cache = cache

    def force_update_ui_geometry(self) -> None:
        self.update_ui_geometry_cache()

    def on_mouse_move(self, x: int | float, y: int | float) -> None:
        kivy_window_height: int = self._base.win.getYSize()  # type: ignore
        _y: int = int(kivy_window_height - y)  # type: ignore

        inside_ui = False
        for _, (ui_x, ui_y, ui_right, ui_top) in self.ui_geometry_cache.items():
            if ui_x <= x <= ui_right and ui_y <= _y <= ui_top:
                inside_ui = True
                break

        current_time = time()
        if current_time - self.last_state_change_time < self.state_change_cooldown:
            return

        if inside_ui and not self.in_collision_with_ui:
            self._set_input_state(raycaster=False, zoom_disabled=self.disable_zoom)
        elif not inside_ui and self.in_collision_with_ui:
            self._set_input_state(raycaster=True, zoom_disabled=not self.disable_zoom)

    def register_non_collidable(self, element: Widget | Layout | Popup) -> None:
        if element not in self.non_collidable_ui:
            self.non_collidable_ui.append(element)
            self.force_update_ui_geometry()

    def unregister_non_collidable(self, element: Widget | Layout | Popup) -> None:
        if element in self.non_collidable_ui:
            self.non_collidable_ui.remove(element)
            self.ui_geometry_cache.pop(element, None)

    def _set_input_state(self, raycaster: bool, zoom_disabled: bool) -> None:
        current_time = time()

        if self.last_raycaster_state != raycaster:
            messenger.send("system.input.raycaster_off" if not raycaster else "system.input.raycaster_on")
            self.last_raycaster_state = raycaster

        if self.disable_zoom and self.last_zoom_state != zoom_disabled:
            messenger.send("system.input.disable_zoom" if zoom_disabled else "system.input.enable_zoom")
            self.last_zoom_state = zoom_disabled

        self.in_collision_with_ui = not raycaster
        self.last_state_change_time = current_time

    def destroy(self) -> None:
        _CollisionPoller.instance().unregister(self)
        if self.in_collision_with_ui:
            self._set_input_state(raycaster=True, zoom_disabled=not self.disable_zoom)
        self.non_collidable_ui.clear()
        self.ui_geometry_cache.clear()
