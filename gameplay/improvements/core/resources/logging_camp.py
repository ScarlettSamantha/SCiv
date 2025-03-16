from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class LoggingCamp(Improvement):
    name = _t("content.improvements.core.resources.logging_camp.name")
    description = _t("content.improvements.core.resources.logging_camp.description")
    placeable_on_tiles = True
    _model = "assets/models/tile_improvements/building_lumbermill_blue.gltf"
    _model_scale = 0.33
    _model_hpr = (45, 0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, gold=1.0, mode=Yields.ADDITIVE)
