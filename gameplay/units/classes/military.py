from typing import TYPE_CHECKING, Any

from gameplay.units.unit import Unit

if TYPE_CHECKING:
    pass


class MilitaryBaseClass(Unit):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
