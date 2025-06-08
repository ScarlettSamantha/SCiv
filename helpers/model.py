import math
from typing import Dict, Optional, Tuple
from panda3d.core import LPoint3f, NodePath, Point3, Vec3

from managers.assets import AssetManager


class ModelHelper:
    asset_manager_cache: AssetManager = AssetManager.get_singleton_instance()
    _position_cache: Dict[Tuple[float, float], Dict[str, Tuple[float, float, float]]] = {}

    @classmethod
    def calculate_hex_slot_positions(
        cls, radius: float = 1.0, slot_radius: float = 0.25
    ) -> Dict[str, Tuple[float, float, float]]:
        if (radius, slot_radius) in cls._position_cache:
            return cls._position_cache[(radius, slot_radius)]

        _corner_dirs = {
            "E": (radius, 0.0),
            "NE": (radius / 2, radius * math.sqrt(3) / 2),
            "NW": (-radius / 2, radius * math.sqrt(3) / 2),
            "W": (-radius, 0.0),
            "SW": (-radius / 2, -radius * math.sqrt(3) / 2),
            "SE": (radius / 2, -radius * math.sqrt(3) / 2),
        }
        cls._position_cache[(radius, slot_radius)] = prop_slots = {
            name: (x, y, slot_radius) for name, (x, y) in _corner_dirs.items()
        }
        return prop_slots

    @classmethod
    def load_model(cls, path: str) -> NodePath:
        return cls.asset_manager_cache.load_model(path)

    @classmethod
    def assess_bounds(cls, node: NodePath) -> tuple[Point3, Point3, Vec3]:
        try:
            bounds: Tuple[LPoint3f, LPoint3f] | None = node.getTightBounds()
            if bounds is None or len(bounds) != 2:
                raise ValueError("Invalid bounds returned from getTightBounds")

            size = bounds[0] - bounds[1]
            return bounds[0], bounds[1], size
        except Exception as e:
            print(f"Error assessing bounds for {node}: {e}")
            return Point3(0, 0, 0), Point3(0, 0, 0), Vec3(0, 0, 0)

    @classmethod
    def compute_uniform_scale(cls, size: Vec3, target_bounds: tuple[float, float, float, float]) -> float:
        """
        Calculate a uniform scale factor so that an object of given size fits within target bounds.

        :param size: Vec3 representing current (width, depth, height)
        :param target_bounds: (min_x, max_x, min_y, max_y) defining the target rectangle in the X-Y plane
        :return: Uniform scale factor
        """
        min_x, max_x, min_y, max_y = target_bounds
        target_width = max_x - min_x
        target_depth = max_y - min_y

        # Avoid division by zero
        scale_x = target_width / size.x if size.x != 0 else float("inf")
        scale_y = target_depth / size.y if size.y != 0 else float("inf")
        return min(scale_x, scale_y)

    @classmethod
    def get_size(cls, node: NodePath) -> Vec3:
        """
        Compute the size (width, depth, height) of a NodePath's tight AABB.

        :param node: The NodePath whose size to compute
        :return: Vec3 representing (width, depth, height)
        """
        bounds = node.getTightBounds()
        if not bounds or len(bounds) != 2:
            raise ValueError("Invalid bounds returned from getTightBounds")
        min_pt, max_pt = bounds
        return max_pt - min_pt

    @classmethod
    def scale_to_bounds(cls, node: NodePath, target_bounds: tuple[float, float, float, float]) -> NodePath:
        """
        Uniformly scale and recenter a NodePath so it fits within the specified X-Y rectangle.

        :param node: The NodePath to scale and recenter
        :param target_bounds: (min_x, max_x, min_y, max_y)
        :return: The same NodePath, scaled and re-centered
        """

        # 1) Assess current bounds
        size = cls.get_size(node)

        # 2) Compute scale
        uniform_scale = cls.compute_uniform_scale(size, target_bounds)
        node.setScale(uniform_scale)

        # 3) Recenter within its own local space
        bounds = node.getTightBounds()
        if not bounds or len(bounds) != 2:
            raise ValueError("Invalid bounds returned from getTightBounds")

        new_min, new_max = bounds
        center = (new_min + new_max) * 0.5
        node.setPos(-center)

        return node

    @classmethod
    def calculate_slot_scale_factor(
        cls,
        node: NodePath,
        slot_name: Optional[str] = None,
        slot_positions: Optional[Tuple[float, float, float]] = None,
        radius: float = 1.0,
        slot_radius: float = 1.0,
    ) -> float:
        if slot_positions is not None and slot_name is None:
            _, _, r = slot_positions
        elif slot_name is not None:
            slots = cls.calculate_hex_slot_positions(radius, slot_radius)
            if slot_name not in slots:
                raise ValueError(f"Unknown slot '{slot_name}'. Valid: {list(slots.keys())}")
            _, _, r = slots[slot_name]
        else:
            r = slot_radius

        size = cls.get_size(node)
        max_dim = max(size.x, size.y, 1e-6)
        scale_factor = (r * 2.0) / max_dim
        return scale_factor

    @classmethod
    def place_in_hex_slot(
        cls,
        node: NodePath,
        slot_name: str,
        slot_positions: Optional[Dict[str, Tuple[float, float, float]]] = None,
        radius: float = 1.0,
        slot_radius: float = 0.25,
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> NodePath:
        slots = cls.calculate_hex_slot_positions(radius, slot_radius) if slot_positions is None else slot_positions
        if slot_name not in slots:
            raise ValueError(f"Unknown slot '{slot_name}'. Valid: {list(slots.keys())}")
        x, y, r = slots[slot_name]

        # Compute uniform scale so the node fits within the slot diameter
        size = cls.get_size(node)
        max_dim = max(size.x, size.y, 1e-6)
        scale_factor = (r * 2.0) / max_dim
        node.setScale(scale_factor)

        # Apply rotation
        node.setHpr(*rotation)

        # Position at slot + offset
        node.setPos(x + offset[0], y + offset[1], offset[2])

        return node
