from gameplay.effects.improvement.farm import FarmEffect
from gameplay.improvement import Improvement
from managers.i18n import _t


class Farm(Improvement):
    name = _t("content.improvements.core.resources.farm.name")
    description = _t("content.improvements.core.resources.farm.description")
    _model = "assets/models/tile_improvements/building_home_A_blue.gltf"
    _model_scale = 0.33
    _model_hpr = (45, 0, 0)
    placeable_on_tiles = True

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.effects.add_effect(FarmEffect())
