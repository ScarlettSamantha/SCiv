from typing import Any
from gameplay.units.unit_base import UnitBaseClass


class CivilianBaseClass(UnitBaseClass):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
