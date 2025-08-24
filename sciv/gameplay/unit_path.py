from math import ceil
from typing import TYPE_CHECKING, Iterable, List, Literal, Optional, Tuple

from direct.task import Task
from helpers.cache import Cache
from helpers.colors import Colors
from panda3d.core import (
    CardMaker,
    LMatrix3f,
    NodePath,
    TransparencyAttrib,
)
from panda3d.core import (
    LVector3f as Vec3,
)
from pandac.PandaModules import LQuaternionf, LVector3f

if TYPE_CHECKING:
    from gameplay.tile import Tile

UP = Vec3(0, 0, 1)


class BlockPathStyle:
    width = 0.04
    block_length = 0.08
    gap_length = 0.08
    speed = 0.45
    hover = 0.06
    color = Colors.RED
    draw_on_top = True


class MovementPathBlocksRenderer:
    def __init__(self, parent: NodePath, style: BlockPathStyle | None = None) -> None:
        self.parent: NodePath = parent
        self.style: BlockPathStyle = style or BlockPathStyle()

        self.target_tile: Optional["Tile"] = None
        self.source_tile: Optional["Tile"] = None

        self._root = NodePath("movement_path_blocks")
        self._root.set_two_sided(True)
        self._root.set_transparency(TransparencyAttrib.M_alpha)
        self._root.set_color(self.style.color)

        self.base = Cache.get_showbase_instance()

        self._root.set_depth_write(False)
        if self.style.draw_on_top:
            self._root.set_depth_test(False)
            self._root.set_bin("fixed", 50)
        else:
            self._root.set_depth_test(True)
            self._root.set_depth_offset(4)

        self._root.set_light_off(1)
        self._root.set_texture_off(1)
        self._root.set_color_off(0)

        self._pts: List[Vec3] = []
        self._dists: List[float] = [0.0]
        self._path_len: float = 0.0

        self._blocks: List[NodePath] = []
        self._phase: float = 0.0
        self._task_name: str = f"MovementPathBlocksRenderer.update-{id(self)}"
        self._visible = False

    def set_path(
        self, points: Iterable[Vec3], source_tile: Optional["Tile"] = None, target: Optional["Tile"] = None
    ) -> None:
        self.source_tile = source_tile
        self.target_tile = target

        pts: List[Vec3] = self._prepare_points(points)
        self._pts = pts
        self._recompute_distances()
        self._ensure_pool()

        self._phase = 0.0
        self._update_blocks(0.0)

    def show(self) -> None:
        if not self._root.get_parent():
            self._root.reparent_to(self.parent)
        if not self._visible:
            self._visible = True
            self._start_task()

    def is_visible(self) -> bool:
        return self._visible

    def hide(self) -> None:
        if self._visible:
            self._visible = False
            self._stop_task()
        self._root.detach_node()

    def clear(self) -> None:
        for np in self._blocks:
            np.remove_node()
        self._blocks.clear()
        self._pts.clear()
        self._dists = [0.0]
        self._path_len = 0.0

    def dispose(self) -> None:
        self.hide()
        self.clear()
        self._root.remove_node()

    def node(self) -> NodePath:
        return self._root

    def _prepare_points(self, points: Iterable[Vec3]) -> List[Vec3]:
        out: List[Vec3] = []
        last: Vec3 | None = None
        for p in points:
            p = Vec3(p)
            if last is None or (p - last).length_squared() > 1e-8:
                out.append(p)
                last = p
        return out

    def _recompute_distances(self) -> None:
        self._dists = [0.0]
        for i in range(1, len(self._pts)):
            self._dists.append(self._dists[-1] + (self._pts[i] - self._pts[i - 1]).length())
        self._path_len = self._dists[-1] if self._pts else 0.0

    def _ensure_pool(self) -> None:
        if self._path_len <= 0.0:
            for np in self._blocks:
                np.stash()
            return

        period: float = max(self.style.block_length + self.style.gap_length, 1e-4)
        base: int = int(ceil(self._path_len / period)) + 6
        needed: int = base * 2

        while len(self._blocks) < needed:
            block: NodePath = self._root.attach_new_node(f"block-{len(self._blocks)}")

            cm = CardMaker("quad")
            cm.set_frame(-0.5, 0.5, 0.0, 1.0)
            quad: NodePath = block.attach_new_node(cm.generate())

            quad.set_p(90)

            block.set_color(self.style.color)
            block.set_transparency(TransparencyAttrib.M_alpha)

            self._blocks.append(block)

    def _start_task(self) -> None:
        self.base.taskMgr.remove(self._task_name)
        self.base.taskMgr.add(self._tick, self._task_name, sort=50)  # type: ignore

    def _stop_task(self) -> None:
        self.base.taskMgr.remove(taskOrName=self._task_name)

    def _tick(self, task: Task.Task) -> Literal[1]:
        from direct.showbase import ShowBaseGlobal

        dt = ShowBaseGlobal.globalClock.get_dt()
        self._update_blocks(dt)
        return Task.cont

    def _update_blocks(self, dt: float) -> None:
        if self._path_len <= 0.0 or not self._blocks:
            return

        block_len: float = self.style.block_length
        gap_len: float = self.style.gap_length
        period: float = block_len + gap_len

        self._phase = (self._phase + self.style.speed * dt) % period
        offset: float = self._phase

        active_i = 0
        dist: float = -offset

        prev_t: Vec3 | None = None
        prev_up: Vec3 | None = None

        while dist < self._path_len and active_i < len(self._blocks):
            s0: float = max(0.0, dist)
            s1: float = min(s0 + block_len, self._path_len)
            if s1 <= s0 + 1e-6:
                break

            active_i, prev_t, prev_up = self._place_span_smooth(active_i, s0, s1, prev_t, prev_up)
            dist += period

        for j in range(active_i, len(self._blocks)):
            self._blocks[j].stash()

    def _place_span(
        self,
        idx: int,
        s0: float,
        s1: float,
        prev_t: Vec3 | None,
        prev_up: Vec3 | None,
    ) -> tuple[int, Vec3 | None, Vec3 | None]:
        if idx >= len(self._blocks):
            return idx, prev_t, prev_up

        p0, _ = self._sample_at(s0)
        p1, _ = self._sample_at(s1)
        seg_vec: LVector3f = p1 - p0
        seg_len: float = max(seg_vec.length(), 1e-6)

        s_mid: float = self._wrap_s(0.5 * (s0 + s1))
        t_mid: LVector3f = self._tangent_at(s_mid)

        up: LVector3f = self._transport_up(prev_t, prev_up, t_mid)
        right: LVector3f = t_mid.cross(up)
        if right.length_squared() < 1e-10:
            right = Vec3(1, 0, 0)
        right.normalize()
        up = right.cross(t_mid)
        up.normalize()

        tail: LVector3f = p0 + UP * self.style.hover

        np: NodePath = self._blocks[idx]
        np.set_pos(tail)
        np.set_quat(self._quat_from_axes(t_mid, up))  # Y -> forward, Z -> up
        np.set_scale(self.style.width, seg_len, 1.0)  # X=width, Y=length
        np.unstash()

        return idx + 1, t_mid, up

    def _place_span_smooth(
        self,
        idx: int,
        s0: float,
        s1: float,
        prev_t: Vec3 | None,
        prev_up: Vec3 | None,
    ) -> tuple[int, Vec3 | None, Vec3 | None]:
        if idx >= len(self._blocks):
            return idx, prev_t, prev_up

        p0, _ = self._sample_at(s0)
        p1, _ = self._sample_at(s1)
        seg_vec: LVector3f = p1 - p0
        seg_len: float = max(seg_vec.length(), 1e-6)

        s_mid: float = 0.5 * (s0 + s1)
        t_mid: LVector3f = self._tangent_at_clamped(s_mid)

        t_end: Vec3 = self._tangent_at_clamped(max(s1 - 1e-4, 0.0))
        shortness: float = max(0.0, 1.0 - (s1 - s0) / self.style.block_length)  # 0..1
        blend: float = min(1.0, shortness * 1.25)  # ease in a bit earlier
        t_dir: Vec3 = t_mid * (1.0 - blend) + t_end * blend
        if t_dir.length_squared() < 1e-10:
            t_dir = t_mid
        else:
            t_dir.normalize()

        up: LVector3f = self._transport_up(prev_t, prev_up, t_dir)
        right: LVector3f = t_dir.cross(up)
        if right.length_squared() < 1e-10:
            right = Vec3(1, 0, 0)
        right.normalize()
        up = right.cross(t_dir)
        up.normalize()

        tail: LVector3f = p0 + UP * self.style.hover

        np: NodePath = self._blocks[idx]
        np.set_pos(tail)

        np.look_at(tail + t_dir, up)

        np.set_scale(self.style.width, seg_len, 1.0)
        np.unstash()

        return idx + 1, t_dir, up

    def _sample_at(self, s: float) -> Tuple[Vec3, Vec3]:
        if s <= 0.0 or len(self._pts) == 1:
            if not self._pts:
                return Vec3(0), Vec3(0, 1, 0)
            t = (self._pts[1] - self._pts[0]) if len(self._pts) > 1 else Vec3(0, 1, 0)
            t.normalize() if t.length_squared() > 1e-12 else None
            return self._pts[0], t

        if s >= self._path_len:
            t = (self._pts[-1] - self._pts[-2]) if len(self._pts) >= 2 else Vec3(0, 1, 0)
            if t.length_squared() > 1e-12:
                t.normalize()
            return self._pts[-1], t

        i = 1
        while i < len(self._dists) and self._dists[i] < s:
            i += 1

        i: int = max(1, i)
        s0: float = self._dists[i - 1]
        s1: float = self._dists[i]
        seg: LVector3f = self._pts[i] - self._pts[i - 1]
        seg_len: float = max((s1 - s0), 1e-9)
        u: float = (s - s0) / seg_len
        pos: LVector3f = self._pts[i - 1] * (1.0 - u) + self._pts[i] * u
        tan: LVector3f = seg / seg_len
        return pos, tan

    @staticmethod
    def _quat_from_axes(forward: Vec3, up: Vec3) -> LQuaternionf:
        right: LVector3f = forward.cross(up)
        right.normalize()
        up = right.cross(forward)
        up.normalize()
        m = LMatrix3f(
            right.x,
            forward.x,
            up.x,
            right.y,
            forward.y,
            up.y,
            right.z,
            forward.z,
            up.z,
        )
        q = LQuaternionf()
        q.set_from_matrix(m)
        return q

    def _wrap_s(self, s: float) -> float:
        if self._path_len <= 0.0:
            return 0.0
        return s % self._path_len

    def _tangent_at(self, s: float) -> Vec3:
        if self._path_len <= 0.0:
            return Vec3(0, 1, 0)
        eps: float = min(max(self.style.block_length * 0.35, 0.04), 0.5)
        s_a: float = self._wrap_s(s - eps)
        s_b: float = self._wrap_s(s + eps)
        p_a, _ = self._sample_at(s_a)
        p_b, _ = self._sample_at(s_b)
        t: LVector3f = p_b - p_a
        if t.length_squared() < 1e-10:
            _, t = self._sample_at(s)
        else:
            t.normalize()
        return t

    def _tangent_at_clamped(self, s: float) -> Vec3:
        if self._path_len <= 0.0:
            return Vec3(0, 1, 0)

        eps: float = min(max(self.style.block_length * 0.35, 0.04), 0.5)
        s_a: float = max(0.0, s - eps)
        s_b: float = min(self._path_len, s + eps)

        p_a, _ = self._sample_at(s_a)
        p_b, _ = self._sample_at(s_b)
        t: Vec3 = p_b - p_a
        if t.length_squared() < 1e-10:
            _, t = self._sample_at(min(max(s, 0.0), self._path_len))
        if t.length_squared() > 1e-12:
            t.normalize()
        else:
            t = Vec3(0, 1, 0)
        return t

    def _transport_up(self, prev_t: Vec3 | None, prev_up: Vec3 | None, t_new: Vec3) -> Vec3:
        if prev_t is None or prev_up is None:
            u: LVector3f = UP - t_new * t_new.dot(UP)
            if u.length_squared() < 1e-6:
                u = Vec3(0, 1, 0)
            u.normalize()
            return u

        k: LVector3f = prev_t.cross(t_new)
        sin_theta: float = k.length()
        cos_theta: float = prev_t.dot(t_new)

        if sin_theta < 1e-6:
            return prev_up

        k.normalize()
        u = prev_up * cos_theta + k.cross(prev_up) * sin_theta + k * (k.dot(prev_up)) * (1.0 - cos_theta)
        if u.length_squared() < 1e-10:
            return prev_up
        u.normalize()
        return u
