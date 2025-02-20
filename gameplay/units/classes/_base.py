from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, LVector3
from direct.showbase.Loader import Loader

from managers.i18n import T_TranslationOrStr
from typing import Optional, Tuple, Type, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from data.tiles.tile import Tile
    from gameplay.promotion import PromotionTree
    from gameplay.player import Player
class UnitBaseClass:
    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        base: ShowBase,
        icon: str | None,
        promotion_tree: Type["PromotionTree"],
        owner: Optional["Player"] = None,
        tile: Optional["Tile"] = None,
        model: Optional[T_TranslationOrStr] = None,
        model_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        model_size: float = 1.0,
        model_position_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        *args: Any,
        **kwargs: Any,
    ):
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description
        self.icon: str | None = icon
        self.promotion_tree: Type[PromotionTree] = promotion_tree
        self.owner: Player | None = owner
        self.tile: Tile | None = tile  # Tile must be set before spawning
        self.model: Optional[NodePath | T_TranslationOrStr] = (
            model  # Will hold the Panda3D model
        )
        self.model_size: float = model_size  # Default size of the model
        self.model_rotation: Tuple[float, float, float] = (
            model_rotation  # Default rotation of the model
        )
        self.model_position_offset: Tuple[float, float, float] = model_position_offset
        self.base: ShowBase = base
        self.colliders = NodePath("colliders")

    def spawn(self) -> bool:
        """
        Spawns the unit at its assigned tile, loading the model into Panda3D.
        Returns True if successful, False otherwise.
        """
        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        if not self.tile.is_occupied():  # Assumed tile method
            raise ValueError(f"Tile at {self.tile.get_cords()} is not passable.")

        if not isinstance(self.model, str):
            raise ValueError(f"Unit {self.key} has no model assigned.")

        # Load the Panda3D model and position it at the tile
        self.model = self.load_model(self.model)

        if not self.model:
            raise RuntimeError(f"Failed to load model for unit {self.key}")

        print(
            f"Unit {self.key} spawned at {self.tile.get_cords()} with model {self.model}"
        )
        return True

    def load_model(self, model_path: str) -> NodePath | None:
        """
        Loads the unit model in Panda3D, places it at the correct position,
        and automatically loads its collision geometry (if available).
        """
        loader: Loader = Loader(self.base)
        model: Optional[NodePath] = loader.loadModel(model_path)
        if not model:
            return None

        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        # Position and transform the model
        tile_pos = self.tile.get_cords()
        pos = (
            tile_pos[0] + self.model_position_offset[0],
            tile_pos[1] + self.model_position_offset[1],
            tile_pos[2] + self.model_position_offset[2],
        )
        model.setPos(LVector3(*pos))
        model.setHpr(LVector3(*self.model_rotation))
        model.setScale(self.model_size)
        self.colliders = model.findAllMatches("**/+CollisionNode")
        if self.colliders.getNumPaths() > 0:
            self.colliders.reparentTo(model)  # Ensure collision nodes are used
        else:
            raise ValueError(
                f"⚠️ No collision detected for {self.key}, consider adding it in GLTF"
            )

        model.reparentTo(self.base.render)  # Attach model to scene graph

        return model
