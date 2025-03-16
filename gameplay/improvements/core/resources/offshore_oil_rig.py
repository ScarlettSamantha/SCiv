from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class OffshoreOilRig(Improvement):
    name = _t("content.improvements.core.resources.offshore_oil_rig.name")
    description = _t("content.improvements.core.resources.offshore_oil_rig.description")
    placeable_on_tiles = True

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="offshore_oil_rig", food=1.0, mode=Yields.ADDITIVE)
