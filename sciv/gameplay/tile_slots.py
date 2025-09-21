from typing import Dict

default_slots: Dict[str, tuple[float, float, float]] = {
    "e": (0.435, 0.0, 0.0),
    "ne": (0.345, 0.35, 0.0),
    "nw": (-0.345, 0.35, 0.0),
    "w": (-0.435, 0.0, 0.0),
    "sw": (-0.345, -0.375, 0.0),
    "se": (0.345, -0.375, 0.0),
    "center": (0.0, 0.0, 0.0),
    "resource": (0.0, 0.0, 0.0),
    "n": (0.0, 0.435, 0.0),
    "s": (0.0, -0.435, 0.0),
}

grid_offset = 0.5
grid_offset_negative = 0 - grid_offset
grid_offset_diagonal = 0.4
grid_offset_diagonal_negative = 0 - grid_offset_diagonal

city_slots: Dict[str, tuple[float, float, float]] = {
    "palace": (0.0, 0.0, 0.0),
    "city_n": (0.0, grid_offset, 0.0),
    "city_s": (0.0, grid_offset_negative, 0.0),
    "city_e": (grid_offset, 0.0, 0.0),
    "city_w": (grid_offset_negative, 0.0, 0.0),
    "city_ne": (grid_offset_diagonal, grid_offset_diagonal, 0.0),
    "city_nw": (grid_offset_diagonal_negative, grid_offset_diagonal, 0.0),
    "city_se": (grid_offset_diagonal, grid_offset_diagonal_negative, 0.0),
    "city_sw": (grid_offset_diagonal_negative, grid_offset_diagonal_negative, 0.0),
}
