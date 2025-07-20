from typing import Any, Literal, Tuple

from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import CardMaker, ColorBlendAttrib, NodePath, PandaNode, Shader, TransparencyAttrib


class HoverIndicator:
    def __init__(
        self,
        parent: NodePath,
        dash_freq: float = 16.0,
        pulse_speed: float = 3.0,
        border_width: float = 0.05,
        color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    ):
        self.root: NodePath = parent.attach_new_node(PandaNode("hover_indicator"))

        cm = CardMaker("indicator_card")
        cm.set_frame(-1, 1, -1, 1)
        self.card: NodePath = self.root.attach_new_node(cm.generate())

        self.shader: Shader = Shader.load(
            lang=Shader.SL_GLSL,
            vertex="assets/shaders/hover_indicator.vert.glsl",
            fragment="assets/shaders/hover_indicator.frag.glsl",
        )
        self.card.set_shader(self.shader)

        self.card.set_transparency(TransparencyAttrib.MAlpha)
        self.card.set_attrib(
            ColorBlendAttrib.make(
                ColorBlendAttrib.MAdd,
                ColorBlendAttrib.OIncomingAlpha,
                ColorBlendAttrib.OOneMinusIncomingAlpha,
            )
        )

        self.card.set_hpr(0, -90, 0)
        self.card.set_z(0.05)
        self.card.set_two_sided(True)

        self.dash_freq = dash_freq
        self.pulse_speed = pulse_speed
        self.border_width = border_width
        self.color = color

        for name, val in (
            ("dashFreq", float(self.dash_freq)),
            ("pulseSpeed", float(self.pulse_speed)),
            ("borderWidth", float(self.border_width)),
            ("color", self.color),
        ):
            self.card.set_shader_input(name, val)  # type: ignore

        self.card.set_shader_input("time", 0.0)  # type: ignore

        taskMgr.add(self._update_time, f"HoverIndicator-update-{id(self)}")  # type: ignore

    def _update_time(self, task: Task.Task) -> Literal[1]:
        self.card.set_shader_input("time", task.time)  # type: ignore
        return Task.cont

    def cleanup(self) -> None:
        taskMgr.remove(f"HoverIndicator-update-{id(self)}")
        if not self.card.is_empty():
            self.card.remove_node()
        if not self.root.is_empty():
            self.root.remove_node()

    @classmethod
    def add_to_entity(cls, entity: NodePath, **kwargs: Any) -> "HoverIndicator":
        return cls(entity, **kwargs)

    @classmethod
    def remove_from_entity(cls, entity: NodePath) -> None:
        node = entity.find("**/hover_indicator")
        if not node.is_empty():
            node.remove_node()
        else:
            raise ValueError("No hover indicator found on the entity.")
