from typing import TYPE_CHECKING, Any

from gameplay.units.unit_base import UnitBaseClass

if TYPE_CHECKING:
    pass


class MilitaryBaseClass(UnitBaseClass):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
