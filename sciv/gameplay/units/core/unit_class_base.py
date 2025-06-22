from typing import Any

from gameplay.unit import Unit


class CoreBaseUnit(Unit):
    pass


class CoreBaseCivilianUnit(CoreBaseUnit):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class CoreBaseMilitaryUnit(CoreBaseUnit):
    pass
