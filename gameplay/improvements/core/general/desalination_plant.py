from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class DesalinationPlant(Improvement):
    name = _t("content.improvements.core.general.desalination_plant.name")
    description = _t("content.improvements.core.general.desalination_plant.description")

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="desalination_plant", food=1.0, mode=Yields.ADDITIVE)
