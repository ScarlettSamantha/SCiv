from typing import Any

from gameplay.units.unit_base import UnitBaseClass


class CoreBaseUnit(UnitBaseClass):
    pass


class CoreBaseCivilianUnit(CoreBaseUnit):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class CoreBaseMilitaryUnit(CoreBaseUnit):
    pass
