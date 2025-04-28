from typing import Any

from gameplay.units.core.classes.military._base import CoreMilitaryBaseClass
from helpers.placeholder import Placeholder
from managers.i18n import t_


class BarbarianLion(CoreMilitaryBaseClass):
    _model = "assets/models/units/barbarian_lion.glb"
    buildable = False
    key = "core.units.military.barbarian.lion"
    name = t_("content.units.units.core.units.military.barbarian.lion.name")
    description = t_("content.units.units.core.units.military.barbarian.lion.name")
    icon = Placeholder.getPlaceholderImagePathSmallIcon()
    model_size = 0.025

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
        self.model_position_offset = (0, 0, 0.1)
