from typing import Any

from gameplay.units.unit_base import UnitBaseClass


class MilitaryBaseClass(UnitBaseClass):
    def __init__(self, base, *args: Any, **kwargs: Any):
        super().__init__(base, *args, **kwargs)
        self._base = base
