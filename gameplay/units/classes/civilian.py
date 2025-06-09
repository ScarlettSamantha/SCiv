from typing import TYPE_CHECKING, Any

from gameplay.unit import Unit

if TYPE_CHECKING:
    from gameplay.tile import Tile


class CivilianBaseClass(Unit):
    def __init__(self, tile: "Tile", *args: Any, **kwargs: Any):
        super().__init__(tile, *args, **kwargs)
