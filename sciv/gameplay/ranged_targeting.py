from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Literal, Optional, cast

from direct.task import Task
from helpers.cache import Cache
from helpers.colors import Colors
from helpers.maths import bezier_pos, bezier_tangent
from panda3d.core import (
    AntialiasAttrib,
    Geom,
    GeomNode,
    GeomTristrips,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    LPoint3f,
    LVector3f,
    LVector4f,
    NodePath,
    Vec3,
)
from system.shaders import Shader, Shaders

if TYPE_CHECKING:
    from sciv.game import OpenCiv


def _build_control_points(a: Vec3, b: Vec3, hump_factor: float) -> tuple[Vec3, Vec3, Vec3, Vec3]:
    p0 = a
    p3 = b

    delta: LVector3f = b - a
    dist: float = max(delta.length(), 1e-3)
    flat_dir = Vec3(delta.x, delta.y, 0.0)
    if flat_dir.length_squared() < 1e-8:
        flat_dir = Vec3(0, 1, 0)
    flat_dir.normalize()

    h: float = max(min(dist * hump_factor, 8.0), 1.0)

    p1: LVector3f = p0 + flat_dir * (dist * 0.25) + Vec3(0, 0, h * 0.5)
    p2: LVector3f = p0 + flat_dir * (dist * 0.75) + Vec3(0, 0, h)

    return p0, p1, p2, p3


def _make_format() -> GeomVertexFormat:
    arr = GeomVertexArrayFormat()
    arr.addColumn(InternalName.make("vertex"), 3, Geom.NTFloat32, Geom.CPoint)
    arr.addColumn(InternalName.make("a_tangent"), 3, Geom.NTFloat32, Geom.COther)
    arr.addColumn(InternalName.make("a_s"), 1, Geom.NTFloat32, Geom.COther)
    arr.addColumn(InternalName.make("a_side"), 1, Geom.NTFloat32, Geom.COther)
    arr.addColumn(InternalName.make("a_v"), 1, Geom.NTFloat32, Geom.COther)
    fmt = GeomVertexFormat()
    fmt.addArray(arr)
    return GeomVertexFormat.registerFormat(fmt)


_TARGET_FMT: GeomVertexFormat = _make_format()


def _resolve_np(obj: Any) -> Optional[NodePath]:
    return obj.model


@dataclass
class RangedTargetingStyle:
    color: tuple[float, float, float, float] = Colors.RED
    width_world: float = 0.05
    edge_feather: float = 0.25
    hump_factor: float = 0.30
    cap_boost: float = 0.25
    cap_ramp: float = 0.22


class RangedTargeting:
    def __init__(self, parent: NodePath, *, style: Optional[RangedTargetingStyle] = None) -> None:
        from helpers.cache import Cache

        self.parent: NodePath = parent
        self.root: NodePath = parent.attachNewNode("ranged-targeting-root")
        self.root.setTransparency(1)
        self.root.setDepthWrite(False)
        self.root.setAntialias(AntialiasAttrib.MAuto)
        self.root.setTwoSided(True)
        self.root.setBin("fixed", 40)  # draw late so it sits above terrain a bit
        self.base: "OpenCiv" = Cache.get_showbase_instance()
        self.task_manager: Task.TaskManager = Cache.get_showbase_instance().taskMgr

        self._active: bool = False

        self.shader_system: Shaders = Shaders()
        self.shader: Shader = self.shader_system.load_shader(
            name="ranged_targeting",
            vert_path=str(self.base.base_path / "assets" / "shaders" / "target_arc.vert.glsl"),
            frag_path=str(self.base.base_path / "assets" / "shaders" / "target_arc.frag.glsl"),
        )

        self.arc_np: Optional[NodePath] = None
        self._src_np: Optional[NodePath] = None
        self._dst_np: Optional[NodePath] = None

        self.style: RangedTargetingStyle = style or RangedTargetingStyle()

        self._last_src = LVector3f(0, 0, 0)
        self._last_dst = LVector3f(0, 0, 0)

        self._task_name = f"ranged-targeting-update-{id(self)}"

    def show(self, source: Any, target: Any) -> None:
        src_np: NodePath | None = _resolve_np(source)
        dst_np: NodePath | None = _resolve_np(target)
        if not src_np or not dst_np or src_np.isEmpty() or dst_np.isEmpty():
            self.hide()
            return

        self._src_np = src_np
        self._dst_np = dst_np
        self._active = True

        self._rebuild_geometry()
        self._apply_uniforms()
        self._ensure_task()

    def hide(self) -> None:
        self._active = False
        self._remove_geom()
        self._cancel_task()

    def destroy(self) -> None:
        self.hide()
        if not self.root.isEmpty():
            self.root.removeNode()

    def _ensure_task(self) -> None:
        if not self.task_manager.hasTaskNamed(taskName=self._task_name):
            self.task_manager.add(self._task_update, self._task_name, extraArgs=[], appendTask=False, sort=40)

    def _cancel_task(self) -> None:
        if self.task_manager.hasTaskNamed(self._task_name):
            self.task_manager.remove(self._task_name)

    def _task_update(self) -> Literal[1]:
        if not self._active or not self._src_np or not self._dst_np:
            return Task.cont

        if self._src_np.isEmpty() or self._dst_np.isEmpty():
            self.hide()
            return Task.cont

        self.root.setShaderInput("u_time", self.base.clock.getFrameTime())  # type: ignore
        self.root.setShaderInput("u_viewport_h", float(self.base.win.getYSize()))  # type: ignore

        cur_src: LPoint3f = self._src_np.get_pos(self.parent)
        cur_dst: LPoint3f = self._dst_np.get_pos(self.parent)
        if (cur_src - self._last_src).length_squared() > 1e-4 or (cur_dst - self._last_dst).length_squared() > 1e-4:
            self._rebuild_geometry()

        return Task.cont

    def _apply_uniforms(self) -> None:
        self.root.setShader(self.shader)
        self.root.setShaderInput("u_color", LVector4f(*self.style.color))  # type: ignore
        self.root.setShaderInput("u_world_up", LVector3f(0.0, 0.0, 1.0))  # type: ignore
        self.root.setShaderInput("u_width_world", float(self.style.width_world))  # type: ignore
        self.root.setShaderInput("u_edge_feather", float(self.style.edge_feather))  # type: ignore
        self.root.setShaderInput("u_cap_boost", float(self.style.cap_boost))  # type: ignore
        self.root.setShaderInput("u_cap_ramp", float(self.style.cap_ramp))  # type: ignore

    def _remove_geom(self) -> None:
        if self.arc_np and not self.arc_np.isEmpty():
            self.arc_np.removeNode()
        self.arc_np = None

    def _rebuild_geometry(self, samples: int = 64) -> None:
        if not (self._src_np and self._dst_np):
            return

        self._remove_geom()

        a: Vec3 = cast(Vec3, self._src_np.get_pos(self.parent) + Vec3(0, 0, 1.4))
        b: Vec3 = cast(Vec3, self._dst_np.get_pos(self.parent) + Vec3(0, 0, 1.4))

        p0, p1, p2, p3 = _build_control_points(a, b, self.style.hump_factor)

        pts: List[Vec3] = []
        tans: List[Vec3] = []
        for i in range(samples):
            t = i / float(samples - 1)
            pts.append(bezier_pos(p0, p1, p2, p3, t))
            tans.append(bezier_tangent(p0, p1, p2, p3, t))

        lengths: List[float] = [0.0]
        total = 0.0

        for i in range(1, samples):
            d: float = (pts[i] - pts[i - 1]).length()
            total += d
            lengths.append(total)

        if total < 1e-6:
            total = 1.0

        s_vals: List[float] = [L / total for L in lengths]

        vdata = GeomVertexData("ranged-targeting", _TARGET_FMT, Geom.UHDynamic)
        vdata.setNumRows(samples * 2)

        base: "OpenCiv" = Cache.get_showbase_instance()
        cam: NodePath = base.cam

        n_views: List[Vec3] = []
        cam_fwd = Vec3(0, -1, 0)  # view-space forward
        prev_n: Optional[Vec3] = None

        for i in range(samples):
            tan_view: Vec3 = cam.getRelativeVector(self.parent, tans[i])
            Vec3.normalize(tan_view)
            Vec3.normalize(cam_fwd)
            t_proj: LVector3f = tan_view - cam_fwd * tan_view.dot(cam_fwd)
            if t_proj.length_squared() < 1e-10:
                n_view = prev_n if prev_n is not None else Vec3(1, 0, 0)
            else:
                t_proj.normalize()
                n_view: LVector3f = cam_fwd.cross(t_proj)
                if n_view.length_squared() < 1e-10:
                    n_view = Vec3(1, 0, 0)
                else:
                    n_view.normalize()

                if prev_n is not None and n_view.dot(prev_n) < 0:
                    n_view = -n_view

            n_views.append(n_view)
            prev_n = n_view

        w_pos = GeomVertexWriter(vdata, "vertex")
        w_tan = GeomVertexWriter(vdata, "a_tangent")
        w_s = GeomVertexWriter(vdata, "a_s")
        w_side = GeomVertexWriter(vdata, "a_side")
        w_v = GeomVertexWriter(vdata, "a_v")

        for i in range(samples):
            pos = pts[i]
            tan = tans[i]
            s = s_vals[i]

            w_pos.addData3f(pos)
            w_tan.addData3f(tan)
            w_s.addData1f(s)
            w_side.addData1f(-1.0)
            w_v.addData1f(0.0)

            w_pos.addData3f(pos)
            w_tan.addData3f(tan)
            w_s.addData1f(s)
            w_side.addData1f(+1.0)
            w_v.addData1f(1.0)

        prim = GeomTristrips(Geom.UHDynamic)
        for idx in range(samples * 2):
            prim.addVertex(idx)
        prim.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode("ranged-targeting-gn")
        node.addGeom(geom)

        self.arc_np = self.root.attachNewNode(node)
        self.arc_np.setShader(self.shader)

        self._apply_uniforms()
        self._last_src = a
        self._last_dst = b

    @classmethod
    def add_to_entity(cls, entity: NodePath, **kwargs: Any) -> "RangedTargeting":
        return cls(entity, **kwargs)
