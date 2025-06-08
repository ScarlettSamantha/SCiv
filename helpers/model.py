from typing import Tuple
from panda3d.core import LPoint3f, NodePath, Point3, Vec3

from managers.assets import AssetManager


class Model:
    asset_manager_cache: AssetManager = AssetManager.get_singleton_instance()

    @classmethod
    def load_model(cls, path: str) -> NodePath:
        """
        Load a model from disk. Replace this implementation with your own asset loader as needed.

        :param path: Path to the model file
        :return: Loaded NodePath
        """
        model = cls.asset_manager_cache.load_model(path)
        return model

    @classmethod
    def assess_bounds(cls, node: NodePath) -> tuple[Point3, Point3, Vec3]:
        """
        Compute the tight axis-aligned bounding box (AABB) of a NodePath.

        :param node: The NodePath whose bounds to assess
        :return: (min_point, max_point, size_vector)
        """
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
