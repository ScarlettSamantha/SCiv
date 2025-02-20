from __future__ import annotations
from typing import Any

from gameplay.units.classes._base import UnitBaseClass


class CoreBaseUnit(UnitBaseClass):
    pass


class CoreBaseCivilianUnit(CoreBaseUnit):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class CoreBaseMilitaryUnit(CoreBaseUnit):
    pass
