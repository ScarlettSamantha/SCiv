from typing import Optional, TYPE_CHECKING, cast
from direct.showbase.Loader import Loader
from direct.task import Task
from panda3d.core import BitMask32, LVector3, NodePath, LineSegs, GeomNode, Shader, Vec4
import numpy as np

from helpers.cache import Cache
from helpers.colors import Tuple4f
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD

if TYPE_CHECKING:
    from gameplay.unit import Unit


class UnitRenderer:
    def __init__(self, unit: "Unit", selection_radius: float = 0.75):
        self.unit: Unit = unit
        self.loader: Loader = Loader(unit.base)
        self.base = Cache.get_showbase_instance()
        self.model_cache: Optional[NodePath] = None
        self.current_model: Optional[NodePath] = None

        # Selection indicator configuration
        self.selection_circle: Optional[NodePath] = None
        self.selection_enabled: bool = False
        self.selection_radius: float = selection_radius
        self._load_selection_shader()
        self.unit.base.taskMgr.add(self._rotate_indicator_task, f"rotate-indicator-{id(self)}")  # type: ignore

    def _load_selection_shader(self):
        try:
            self.selection_shader = Shader.load(
                Shader.SL_GLSL,
                vertex="assets/shaders/unit_selection.vert.glsl",
                fragment="assets/shaders/unit_selection.frag.glsl",
            )
        except Exception:
            self.selection_shader = None

    def get_node(self) -> Optional[NodePath]:
        return self.current_model

    def load_model(self) -> NodePath:
        path = self.unit.get_model_path()
        if not path:
            raise ValueError(f"Unit {self.unit.key} has no model path")

        if not self.model_cache:
            self.model_cache = self.loader.loadModel(path)

        if self.model_cache is None:
            raise ValueError(f"Failed to load model for unit {self.unit.key} at path {path}")

        model = self.model_cache.copyTo(self.unit.base.render)
        self._configure_model(model)
        return model

    def _configure_model(self, model: NodePath) -> None:
        # position and scale
        tile = self.unit.get_tile()
        x, y, z = tile.get_cords()[0], tile.get_cords()[1], tile.calculate_z_pos_on_altitude()[2]
        model.setPos(x, y, z)
        model.setHpr(LVector3(*self.unit.model_rotation))
        model.setScale(self.unit.model_size)
        # collision
        mask = BitMask32.bit(1) if self.unit.collides is True else BitMask32.allOff()
        model.setCollideMask(mask)
        # network tags
        model.setTag(NET_TYPE_FIELD, NET_TYPE.UNIT.value)
        model.setTag(NET_NODE_TAG_ID_FIELD, self.unit.tag)

    def _create_selection_circle(
        self,
        num_segments: int = 64,
        dash_length: int = 2,
        color: Optional[Tuple4f] = None,
        line_thickness: float = 12.0,
    ) -> NodePath:
        segs = LineSegs()

        segs.setThickness(line_thickness)
        segs.setColor(
            cast(
                Vec4,
                self.unit.get_owner().color,
            )
            if color is None
            else Vec4(*color)  # type: ignore
        )
        num_segments = num_segments if num_segments > 0 else 64

        radius = self.selection_radius
        angle_step = 360.0 / num_segments
        dash_length = dash_length if dash_length > 0 else 2

        for i in range(num_segments):
            if (i // dash_length) % 2 == 0:
                angle1 = np.radians(i * angle_step)
                angle2 = np.radians((i + 1) * angle_step)
                segs.moveTo(radius * np.cos(angle1), radius * np.sin(angle1), 0.0)
                segs.drawTo(radius * np.cos(angle2), radius * np.sin(angle2), 0.0)

        node = segs.create()
        circle_np = NodePath(GeomNode(f"sel-circle-{id(self)}"))
        circle_np.node().addGeomsFrom(node)
        circle_np.setHpr(90, 0, 0)

        circle_np.setPos(self.unit.pos_x, self.unit.pos_y, self.unit.pos_z + 0.1)

        if self.selection_shader:
            circle_np.setShader(self.selection_shader)
            circle_np.setShaderInput("dashLength", dash_length)  # type: ignore
            circle_np.setShaderInput("dashFreq", 18.0)  # type: ignore
            circle_np.setShaderInput("pulseSpeed", 2.0)  # type: ignore
            circle_np.setShaderInput("borderWidth", 0.1)  # type: ignore
            circle_np.setShaderInput("radius", self.selection_radius)  # type: ignore
            circle_np.setShaderInput("time", 0.0)  # type: ignore
            circle_np.setShaderInput("color", (0, 0, 0, 0))  # type: ignore

        parent = self.unit.base.render
        circle_np.reparentTo(parent)
        return circle_np

    def _rotate_indicator_task(self, task: Task.Task) -> Task.Task:
        if self.selection_enabled and self.selection_circle:
            # rotate around Z axis
            self.selection_circle.setH(task.time * 60.0)
        return Task.cont  # type: ignore

    def toggle_selection_indicator(self, enable: bool) -> None:
        if enable and not self.selection_circle:
            self.selection_circle = self._create_selection_circle()
        elif not enable and self.selection_circle:
            self.selection_circle.removeNode()
            self.selection_circle = None
        self.selection_enabled = enable

    def get_unit(self) -> "Unit":
        return self.unit

    def render(self) -> NodePath:
        # unload old
        if self.current_model:
            self.unload()
        self.current_model = self.load_model()
        # reparent indicator if active
        if self.selection_enabled and self.selection_circle:
            self.selection_circle.show()
        return self.current_model

    def unload(self) -> None:
        if self.current_model:
            if self.selection_circle:
                self.selection_circle.hide()
            self.current_model.removeNode()
            self.current_model = None

    def update_position(self):
        if not self.current_model:
            return
        x, y, z = self.unit.get_tile().calculate_z_pos_on_altitude()
        self.current_model.setPos(x, y, z)

    def spawn(self) -> NodePath:
        return self.render()

    def destroy(self):
        if self.current_model:
            self.current_model.removeNode()
            self.current_model = None
        if self.model_cache:
            self.model_cache.removeNode()
            self.model_cache = None
        self.unit.base.taskMgr.remove(f"rotate-indicator-{id(self)}")
        if self.selection_circle:
            self.selection_circle.removeNode()
            self.selection_circle = None
