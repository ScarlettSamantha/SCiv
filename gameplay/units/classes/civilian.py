from typing import TYPE_CHECKING, Any

from gameplay.units.unit import Unit

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile


class CivilianBaseClass(Unit):
    def __init__(self, tile: "BaseTile", *args: Any, **kwargs: Any):
        super().__init__(tile, *args, **kwargs)
