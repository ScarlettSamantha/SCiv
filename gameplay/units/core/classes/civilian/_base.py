from typing import Any

from gameplay.tile import Tile
from gameplay.units.classes.civilian import CivilianBaseClass


class CoreCivilianBaseClass(CivilianBaseClass):
    def __init__(self, tile: "Tile", *args: Any, **kwargs: Any):
        super().__init__(tile, *args, **kwargs)
