from collections.abc import Callable
from dataclasses import dataclass
from itertools import count
from typing import TYPE_CHECKING

from direct.task import Task
from helpers.cache import Cache
from panda3d.core import NodePath

if TYPE_CHECKING:
    from sciv.game import OpenCiv


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(slots=True, frozen=True)
class ZoomVisibilityRule:
    min_zoom: float | None = None
    max_zoom: float | None = None
    fade_in: float = 0.0
    fade_out: float = 0.0


def compute_zoom_visibility_alpha(zoom: float, rule: ZoomVisibilityRule) -> float:
    alpha: float = 1.0

    if rule.min_zoom is not None:
        if zoom < rule.min_zoom:
            if rule.fade_in <= 0.0:
                return 0.0

            fade_start = rule.min_zoom - rule.fade_in
            if zoom <= fade_start:
                return 0.0

            alpha *= _clamp01((zoom - fade_start) / rule.fade_in)

    if rule.max_zoom is not None:
        if zoom > rule.max_zoom:
            if rule.fade_out <= 0.0:
                return 0.0

            fade_end = rule.max_zoom + rule.fade_out
            if zoom >= fade_end:
                return 0.0

            alpha *= _clamp01(1.0 - ((zoom - rule.max_zoom) / rule.fade_out))

    return _clamp01(alpha)


ZoomVisibilityCallback = Callable[[float, bool, float], None]


@dataclass(slots=True)
class _ZoomVisibilityBinding:
    binding_id: int
    rule: ZoomVisibilityRule
    callback: ZoomVisibilityCallback
    node: NodePath | None = None
    last_alpha: float = -1.0
    last_visible: bool = False


class ZoomVisibilityController:
    _instance: "ZoomVisibilityController | None" = None
    _binding_ids = count(1)

    @classmethod
    def get(cls) -> "ZoomVisibilityController":
        instance = cls._instance
        if instance is None:
            instance = cls()
            cls._instance = instance
        return instance

    def __init__(self) -> None:
        self.base: OpenCiv = Cache.get_showbase_instance()
        self._bindings: dict[int, _ZoomVisibilityBinding] = {}
        self._task_name = "zoomVisibilityControllerTask"

        if not self.base.taskMgr.hasTaskNamed(self._task_name):  # type: ignore[attr-defined]
            self.base.taskMgr.add(self._update, self._task_name)  # type: ignore[attr-defined]

    def register_callback(self, rule: ZoomVisibilityRule, callback: ZoomVisibilityCallback) -> int:
        binding_id = next(self._binding_ids)
        binding = _ZoomVisibilityBinding(binding_id=binding_id, rule=rule, callback=callback)
        self._bindings[binding_id] = binding
        self._apply_binding(binding, float(self.base.get_camera().zoom))
        return binding_id

    def register_node(
        self,
        node: NodePath,
        rule: ZoomVisibilityRule,
        *,
        base_alpha: float = 1.0,
        hide_when_zero: bool = True,
    ) -> int:
        def _apply(alpha: float, visible: bool, _zoom: float, *, target: NodePath = node) -> None:
            if target.is_empty():
                return

            target.setColorScale(1.0, 1.0, 1.0, _clamp01(alpha * base_alpha))

            if visible:
                target.show()
            elif hide_when_zero:
                target.hide()

        binding_id = self.register_callback(rule, _apply)
        binding = self._bindings.get(binding_id)
        if binding is not None:
            binding.node = node
        return binding_id

    def unregister(self, binding_id: int) -> None:
        self._bindings.pop(binding_id, None)

    def refresh(self, binding_id: int) -> None:
        binding = self._bindings.get(binding_id)
        if binding is None:
            return

        binding.last_alpha = -1.0
        binding.last_visible = False
        self._apply_binding(binding, float(self.base.get_camera().zoom))

    def clear(self) -> None:
        self._bindings.clear()

    def _apply_binding(self, binding: _ZoomVisibilityBinding, zoom: float) -> None:
        alpha = compute_zoom_visibility_alpha(zoom, binding.rule)
        visible = alpha > 0.001

        if abs(alpha - binding.last_alpha) <= 0.0001 and visible == binding.last_visible:
            return

        binding.callback(alpha, visible, zoom)
        binding.last_alpha = alpha
        binding.last_visible = visible

    def _update(self, task: Task.Task) -> Task.Task:
        zoom = float(self.base.get_camera().zoom)
        stale: list[int] = []

        for binding_id, binding in self._bindings.items():
            if binding.node is not None and binding.node.is_empty():
                stale.append(binding_id)
                continue

            self._apply_binding(binding, zoom)

        for binding_id in stale:
            self.unregister(binding_id)

        return Task.cont  # type: ignore[return-value]
