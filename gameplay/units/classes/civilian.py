from typing import TYPE_CHECKING, Any

from gameplay.units.unit_base import UnitBaseClass

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile


class CivilianBaseClass(UnitBaseClass):
    def __init__(self, tile: "BaseTile", *args: Any, **kwargs: Any):
        super().__init__(tile, *args, **kwargs)
