from panda3d.core import NodePath, LODNode
from typing import Final


class SceneOptimizer:
    """
    Microservice to optimize Panda3D scene graphs for CPU performance.
    """

    __slots__ = ()

    @staticmethod
    def flatten_scene(root: NodePath) -> None:
        """
        Collapse transform nodes and merge Geoms sharing render attributes.
        """
        # flattenMedium is a good balance; flattenStrong can merge too aggressively
        root.flattenMedium()

    @staticmethod
    def setup_lod(
        parent: NodePath, high: NodePath, mid: NodePath, low: NodePath, in_dist: float = 50.0, out_dist: float = 100.0
    ) -> None:
        """
        Attach high-, mid-, low-poly models to an LODNode under `parent`.
        """
        lod_node = LODNode(f"{parent.get_name()}-lod")
        lod_np = parent.attach_new_node(lod_node)
        lod_np.set_name("lod_root")

        # In-range: high detail
        lod_node.add_switch(in_dist, 0.0)
        high.reparent_to(lod_np)

        # Mid-range
        lod_node.add_switch(out_dist, in_dist)
        mid.reparent_to(lod_np)

        # Far: low detail
        lod_node.add_switch(1000.0, out_dist)
        low.reparent_to(lod_np)

    @staticmethod
    def enable_instancing(model: NodePath, count: int) -> None:
        """
        Turn a repeated model into a GPU instance for faster draw calls.
        """
        model.set_instance_count(count)
