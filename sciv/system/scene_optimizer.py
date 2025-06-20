from panda3d.core import NodePath, LODNode


class SceneOptimizer:
    __slots__ = ()

    @staticmethod
    def flatten_scene(root: NodePath) -> None:
        # root.flatten_light()  # This breaks the game
        pass

    @staticmethod
    def setup_lod(
        parent: NodePath, high: NodePath, mid: NodePath, low: NodePath, in_dist: float = 50.0, out_dist: float = 100.0
    ) -> None:
        lod_node: LODNode = LODNode(f"{parent.get_name()}-lod")  # type: ignore
        lod_np: NodePath = parent.attach_new_node(lod_node)  # type: ignore
        lod_np.set_name("lod_root")  # type: ignore

        # In-range: high detail
        lod_node.add_switch(in_dist, 0.0)  # type: ignore
        high.reparent_to(lod_np)  # type: ignore

        # Mid-range
        lod_node.add_switch(out_dist, in_dist)  # type: ignore
        mid.reparent_to(lod_np)  # type: ignore

        # Far: low detail
        lod_node.add_switch(1000.0, out_dist)  # type: ignore
        low.reparent_to(lod_np)  # type: ignore

    @staticmethod
    def enable_instancing(model: NodePath, count: int) -> None:
        model.set_instance_count(count)  # type: ignore
