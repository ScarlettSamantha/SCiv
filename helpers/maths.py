import math


def scale_value(
    value: float,
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
) -> float:
    if old_max == old_min:
        raise ValueError("old_max and old_min must differ to avoid division by zero")
    normalized = (value - old_min) / (old_max - old_min)
    result = normalized * (new_max - new_min) + new_min
    if math.isnan(result) or math.isinf(result):
        print(f"scale_value produced bad value: {result} from {value=}, {old_min=}, {old_max=}, {new_min=}, {new_max=}")
        return new_min  # Or some other fallback
    return result


def scaled_pos_z(val: float, out_min: float, out_max: float, z_scale: float) -> float:
    center = (out_min + out_max) / 2
    result = center + (val - center) * z_scale
    if math.isnan(result) or math.isinf(result):
        print(f"scaled_pos_z produced bad value: {result} from {val=}, {out_min=}, {out_max=}, {z_scale=}")
        return center  # Or some other fallback
    return result
