from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class DesalinationPlant(Improvement):
    name = t_("content.improvements.core.general.desalination_plant.name")
    description = t_("content.improvements.core.general.desalination_plant.description")
    tile_yield_improvement = Yields(name="desalination_plant", food=1.0, mode=Yields.ADDITIVE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50
