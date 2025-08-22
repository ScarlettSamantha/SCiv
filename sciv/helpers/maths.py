import math

from panda3d.core import Vec3
from pandac.PandaModules import LVector3f


def scale_value(
    value: float,
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
) -> float:
    if old_max == old_min:
        raise ValueError("old_max and old_min must differ to avoid division by zero")
    normalized: float = (value - old_min) / (old_max - old_min)
    result: float = normalized * (new_max - new_min) + new_min
    if math.isnan(result) or math.isinf(result):
        print(f"scale_value produced bad value: {result} from {value=}, {old_min=}, {old_max=}, {new_min=}, {new_max=}")
        return new_min  # Or some other fallback
    return result


def scaled_pos_z(val: float, out_min: float, out_max: float, z_scale: float) -> float:
    center: float = max(0, (out_min + out_max) / 2)
    result: float = center + (val - center) * z_scale
    if math.isnan(result) or math.isinf(result):
        print(f"scaled_pos_z produced bad value: {result} from {val=}, {out_min=}, {out_max=}, {z_scale=}")
        return center  # Or some other fallback
    return result


def bezier_pos(p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, t: float) -> Vec3:
    u: float = 1.0 - t
    return p0 * (u * u * u) + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * (t * t * t)


def bezier_tangent(p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, t: float) -> Vec3:
    u: float = 1.0 - t
    d: LVector3f = (p1 - p0) * (3.0 * u * u) + (p2 - p1) * (6.0 * u * t) + (p3 - p2) * (3.0 * t * t)
    if d.length_squared() == 0:
        return Vec3(0, 1, 0)
    d.normalize()
    return d
