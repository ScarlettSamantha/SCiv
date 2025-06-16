from typing import Optional, TYPE_CHECKING
from direct.showbase.Loader import Loader
from panda3d.core import BitMask32, LVector3, NodePath

from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD

if TYPE_CHECKING:
    from gameplay.unit import Unit


class UnitRenderer:
    def __init__(self, unit: "Unit"):
        self.unit: Unit = unit
        self.loader: Loader = Loader(unit.base)
        self.model_cache: Optional[NodePath] = None
        self.current_model: Optional[NodePath] = None

    def get_node(self) -> Optional[NodePath]:
        """
        Returns the current model node if it exists, otherwise None.
        """
        return self.current_model if self.current_model else None

    def load_model(self) -> NodePath:
        path = self.unit.get_model_path()
        if not path:
            raise ValueError(f"Unit {self.unit.key} has no model path")

        if not self.model_cache:
            self.model_cache = self.loader.loadModel(path)

        if self.model_cache is None:
            raise ValueError(f"Failed to load model for unit {self.unit.key} at path {path}")

        model = self.model_cache.copyTo(self.unit.base.render)
        self._configure_model(model)
        return model

    def _configure_model(self, model: NodePath) -> None:
        # position and scale
        tile = self.unit.get_tile()
        x, y, z = tile.get_cords()[0], tile.get_cords()[1], tile.calculate_z_pos_on_altitude()[2]
        model.setPos(x, y, z)
        model.setHpr(LVector3(*self.unit.model_rotation))
        model.setScale(self.unit.model_size)
        # collision
        mask = BitMask32.bit(1) if self.unit.collides is True else BitMask32.allOff()
        model.setCollideMask(mask)
        # network tags
        model.setTag(NET_TYPE_FIELD, NET_TYPE.UNIT.value)
        model.setTag(NET_NODE_TAG_ID_FIELD, self.unit.tag)

    def get_unit(self) -> "Unit":
        return self.unit

    def render(self) -> NodePath:
        # unload old
        if self.current_model:
            self.unload()
        self.current_model = self.load_model()
        return self.current_model

    def unload(self) -> None:
        if self.current_model:
            self.current_model.removeNode()
            self.current_model = None

    def update_position(self):
        if not self.current_model:
            return
        x, y, z = self.unit.get_tile().calculate_z_pos_on_altitude()
        self.current_model.setPos(x, y, z)

    def spawn(self) -> NodePath:
        return self.render()

    def destroy(self):
        if self.current_model:
            self.current_model.removeNode()
            self.current_model = None
        if self.model_cache:
            self.model_cache.removeNode()
            self.model_cache = None
