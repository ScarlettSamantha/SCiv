"""Hex-grid geometry helpers for the standalone worldgen viewer."""

import math

from PyQt6.QtCore import QPointF

from worldgen_viewer_support import HexCoord


HEX_RADIUS = 18.0
SQRT3 = 3**0.5
HEX_VERTEX_ANGLES = (0, 60, 120, 180, 240, 300)


def _hex_center(coord: HexCoord) -> QPointF:
    col, row = coord
    x = HEX_RADIUS * 1.5 * col
    y = HEX_RADIUS * SQRT3 * (row + 0.5 * (col & 1))
    return QPointF(x, y)


def _hex_polygon(coord: HexCoord) -> list[QPointF]:
    center = _hex_center(coord)
    points: list[QPointF] = []
    for angle in HEX_VERTEX_ANGLES:
        radians = math.radians(angle)
        points.append(QPointF(center.x() + HEX_RADIUS * math.cos(radians), center.y() + HEX_RADIUS * math.sin(radians)))
    return points


def _river_line(coord: HexCoord, side: str) -> tuple[QPointF, QPointF]:
    start_point, end_point = _edge_points_for_side(coord, side)
    inset = 0.18
    return (
        QPointF(
            start_point.x() + (end_point.x() - start_point.x()) * inset,
            start_point.y() + (end_point.y() - start_point.y()) * inset,
        ),
        QPointF(
            end_point.x() + (start_point.x() - end_point.x()) * inset,
            end_point.y() + (start_point.y() - end_point.y()) * inset,
        ),
    )


def _river_segment_key(coord: HexCoord, edge: dict[str, object], side: str) -> tuple[tuple[int, int], tuple[int, int]] | tuple[HexCoord, str]:
    between = edge.get("between")
    if isinstance(between, list) and len(between) == 2:
        first = _coord_from_between_value(between[0])
        second = _coord_from_between_value(between[1])
        if first is not None and second is not None:
            return tuple(sorted((first, second)))
    return coord, side


def _edge_points_for_side(coord: HexCoord, side: str) -> tuple[QPointF, QPointF]:
    polygon = _hex_polygon(coord)
    center = _hex_center(coord)
    neighbor_coord = _neighbor_coord_for_side(coord, side)
    if neighbor_coord is None:
        return polygon[0], polygon[1]

    neighbor_center = _hex_center(neighbor_coord)
    target_midpoint = QPointF((center.x() + neighbor_center.x()) / 2, (center.y() + neighbor_center.y()) / 2)

    best_index = 0
    best_distance = float("inf")
    for index, start_point in enumerate(polygon):
        end_point = polygon[(index + 1) % len(polygon)]
        midpoint = QPointF((start_point.x() + end_point.x()) / 2, (start_point.y() + end_point.y()) / 2)
        distance = (midpoint.x() - target_midpoint.x()) ** 2 + (midpoint.y() - target_midpoint.y()) ** 2
        if distance < best_distance:
            best_distance = distance
            best_index = index

    return polygon[best_index], polygon[(best_index + 1) % len(polygon)]


def _neighbor_coord_for_side(coord: HexCoord, side: str) -> HexCoord | None:
    col, row = coord
    odd_column = (col % 2) == 1

    if side == "east":
        return col, row + 1
    if side == "west":
        return col, row - 1
    if side == "north_west":
        return col - 1, row if odd_column else row - 1
    if side == "north_east":
        return col - 1, row + 1 if odd_column else row
    if side == "south_west":
        return col + 1, row if odd_column else row - 1
    if side == "south_east":
        return col + 1, row + 1 if odd_column else row
    return None


def _coord_from_between_value(value: object) -> HexCoord | None:
    if not isinstance(value, list | tuple) or len(value) != 2:
        return None
    first, second = value
    if not isinstance(first, int) or not isinstance(second, int):
        return None
    return first, second
