from typing import Any

from gameplay.tiles.base_tile import BaseTile
from gameplay.units.classes.civilian import CivilianBaseClass


class CoreCivilianBaseClass(CivilianBaseClass):
    def __init__(self, tile: "BaseTile", *args: Any, **kwargs: Any):
        super().__init__(tile, *args, **kwargs)
