from typing import Any

from gameplay.units.classes.civilian import CivilianBaseClass


class CoreCivilianBaseClass(CivilianBaseClass):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
