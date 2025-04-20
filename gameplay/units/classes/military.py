from typing import TYPE_CHECKING, Any

from gameplay.units.unit_base import UnitBaseClass

if TYPE_CHECKING:
    from main import SCIV


class MilitaryBaseClass(UnitBaseClass):
    def __init__(self, base: "SCIV", *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._base = base
